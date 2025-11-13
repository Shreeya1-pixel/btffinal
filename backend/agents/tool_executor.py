"""
Tool executor agent that runs tools and processes results.
"""

from typing import Any, Optional
import time
import json
from openai import AsyncOpenAI

from backend.agents.base import BaseAgent, AgentRole, AgentResponse
from backend.tools.base import tool_registry
from backend.config import settings
from backend.core.redis_client import redis_client
from backend.core.logger import get_logger

logger = get_logger(__name__)


class ToolExecutorAgent(BaseAgent):
    """
    Agent that executes tools based on query requirements.
    """
    
    def __init__(self, module: str = "generic"):
        super().__init__(
            name=f"ToolExecutor-{module}",
            role=AgentRole.TOOL_EXECUTOR,
            instructions=f"""You are a tool executor agent for the {module} module.

Your responsibilities:
1. Analyze the user's query and context
2. Select appropriate tools to fulfill the request
3. Execute tools in the correct sequence
4. Combine results to answer the query

Available tools: {[t.name for t in tool_registry.get_tools_by_module(module)]}

Always explain which tools you're using and why."""
        )
        self.module = module
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
    async def execute(
        self, 
        query: str, 
        context: Optional[dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute tools to fulfill the query.
        
        Args:
            query: User query
            context: Optional context from orchestrator
            
        Returns:
            AgentResponse with tool results
        """
        trace = self.create_trace()
        start_time = time.time()
        
        try:
            # Get available tools for this module
            tools = tool_registry.get_tools_by_module(self.module)
            tool_schemas = [tool.to_schema() for tool in tools]
            
            messages = [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": query}
            ]
            
            # Use function calling to execute tools
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=[{"type": "function", "function": schema} for schema in tool_schemas],
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            tool_calls = message.tool_calls or []
            
            # Execute each tool call
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                trace.tools_called.append(tool_name)
                logger.info("executing_tool", tool=tool_name, args=tool_args)
                
                tool_def = tool_registry.get_tool(tool_name)
                result = await tool_def.function(**tool_args)
                
                tool_results.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                })

                # Publish tool_result event to Redis bus
                try:
                    await redis_client.publish_agent_event(
                        (context or {}).get("channel", "neuroverse"),
                        {"type": "tool_result", "agent": self.name, "tool": tool_name},
                    )
                except Exception:
                    pass
                
                # Add tool result to conversation
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call.model_dump()]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            
            # Get final response after tool execution
            if tool_calls:
                final_response = await self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages
                )
                content = final_response.choices[0].message.content or ""
            else:
                content = message.content or "No tools were needed for this query."
            
            trace.duration_ms = (time.time() - start_time) * 1000
            trace.metadata = {
                "module": self.module,
                "tool_results": tool_results
            }
            
            logger.info(
                "tool_executor_completed",
                module=self.module,
                tools_executed=len(tool_calls),
                duration_ms=trace.duration_ms
            )
            
            return AgentResponse(
                content=content,
                traces=[trace],
                metadata={
                    "tool_results": tool_results,
                    "module": self.module
                }
            )
            
        except Exception as e:
            logger.error("tool_executor_failed", error=str(e), module=self.module)
            raise

