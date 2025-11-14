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
        
    def _detect_tool_from_query(self, query: str) -> Optional[tuple[str, dict]]:
        """
        Keyword-based tool detection for life-manager queries.
        
        Detects:
        - Communication channel (whatsapp, email, gmail, instagram)
        - Action (send, draft)
        - Recipient (contact name or direct identifier)
        - Message content
        
        Returns:
            (tool_name, arguments_dict) or None if no clear match
        """
        if self.module != "life-manager":
            return None
            
        import re
        query_lower = query.lower()
        
        # Determine if draft or direct send
        is_draft = "draft" in query_lower
        action_suffix = "draft" if is_draft else "send"
        
        # Extract recipient - pattern: "to <name>" or "message <name>" or "<name> on whatsapp"
        recipient = None
        recipient_patterns = [
            r'to\s+([a-zA-Z]+)',  # "to mom", "to boss" - single word only
            r'message\s+([a-zA-Z]+)',  # "message mom"
            r'dm\s+([a-zA-Z]+)',  # "dm mom"
            r'send\s+[^to]*\s+([a-zA-Z]+)\s+on',  # "send hi to mom on" - stops at "on"
            r'([a-zA-Z]+)\s+on\s+whatsapp',  # "mom on whatsapp" - stops at "on"
            r'whatsapp\s+([a-zA-Z]+)',  # "whatsapp mom"
            r'([a-zA-Z]+)\s+on\s+wa',  # "mom on wa"
        ]
        for pattern in recipient_patterns:
            match = re.search(pattern, query_lower)
            if match:
                recipient = match.group(1).strip()
                # Skip if it looks like a phone number (contains digits) or common words
                if not re.search(r'\d', recipient) and recipient not in ['hi', 'hello', 'send', 'message', 'the', 'a', 'an']:
                    break
                else:
                    recipient = None
        
        # Extract message content - everything in quotes or after "saying" or between "send" and "to"
        message = None
        # Try quoted content first
        quote_match = re.search(r'["\']([^"\']+)["\']', query)
        if quote_match:
            message = quote_match.group(1)
        elif "saying" in query_lower:
            parts = query.split("saying", 1)
            if len(parts) > 1:
                message = parts[1].strip().strip('"\'.,')
        elif "send" in query_lower and "to" in query_lower:
            # Extract everything between "send" and "to"
            # Pattern: "send <message> to <name>"
            send_match = re.search(r'send\s+(.+?)\s+to\s+', query_lower)
            if send_match:
                message = send_match.group(1).strip()
                # Remove common words
                message = re.sub(r'\b(a|an|the|on|via|whatsapp|wa|gmail|email|instagram)\b', '', message).strip()
                if not message or len(message) > 50:
                    message = None
        
        # Default message if not found
        if not message:
            message = "hi"
        
        if not recipient:
            recipient = "unknown"
        
        # WhatsApp detection
        if "whatsapp" in query_lower:
            tool_name = f"draft_whatsapp" if is_draft else "send_whatsapp"
            return (tool_name, {"to": recipient, "message": message})
        
        # Gmail/Email detection
        if "gmail" in query_lower or "email" in query_lower:
            # For email, we need subject - try to extract or use default
            subject = "Quick message"
            if "subject" in query_lower:
                subj_match = re.search(r'subject[:\s]+([^,\.]+)', query_lower)
                if subj_match:
                    subject = subj_match.group(1).strip()
            
            tool_name = f"draft_gmail" if is_draft else "send_gmail"
            return (tool_name, {"to": recipient, "subject": subject, "body": message})
        
        # Instagram detection
        if "instagram" in query_lower or "insta" in query_lower:
            tool_name = f"draft_instagram" if is_draft else "send_instagram"
            return (tool_name, {"to": recipient, "message": message})
        
        return None
        
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
            # Try keyword-based tool detection first (for life-manager)
            detected_tool = self._detect_tool_from_query(query)
            
            if detected_tool:
                tool_name, tool_args = detected_tool
                trace.tools_called.append(tool_name)
                logger.info("executing_tool_direct", tool=tool_name, args=tool_args, method="keyword_detection")
                
                tool_def = tool_registry.get_tool(tool_name)
                result = await tool_def.function(**tool_args)
                
                tool_results = [{
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                }]
                
                # Publish tool_result event
                try:
                    await redis_client.publish_agent_event(
                        (context or {}).get("channel", "neuroverse"),
                        {"type": "tool_result", "agent": self.name, "tool": tool_name},
                    )
                except Exception:
                    pass
                
                # Parse result to create content
                try:
                    result_data = json.loads(result)
                    content = json.dumps(result_data, indent=2)
                except:
                    content = str(result)
                
                trace.duration_ms = (time.time() - start_time) * 1000
                trace.metadata = {
                    "module": self.module,
                    "tool_results": tool_results,
                    "direct_execution": True
                }
                
                logger.info(
                    "tool_executor_completed_direct",
                    module=self.module,
                    tool=tool_name,
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
            
            # Fall back to LLM-based tool selection
            # Get available tools for this module
            tools = tool_registry.get_tools_by_module(self.module)
            tool_schemas = [tool.to_schema() for tool in tools]
            
            messages = [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": query}
            ]
            
            # Use function calling to execute tools
            response = await self.client.chat.completions.create(
                model="gpt-4o",
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
                    model="gpt-4o",
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

