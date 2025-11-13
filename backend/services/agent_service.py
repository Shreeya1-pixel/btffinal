"""
Main agent service orchestrating multi-agent workflows.
"""

from typing import Any, Optional
import time

from backend.agents.base import AgentResponse
from backend.agents.orchestrator import OrchestratorAgent
from backend.agents.tool_executor import ToolExecutorAgent
from backend.agents.team_orchestrator import TeamOrchestrator
from backend.services.session_manager import session_manager
from backend.core.redis_client import redis_client
from backend.core.logger import get_logger

logger = get_logger(__name__)


class AgentService:
    """
    Main service for coordinating agent workflows and tool execution.
    """
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.executors = {
            "generic": ToolExecutorAgent("generic"),
            "gis-anomaly": ToolExecutorAgent("gis-anomaly")
        }
        self.team_orchestrator = TeamOrchestrator()
        
    async def process_query(
        self, 
        query: str, 
        session_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Process a user query through the agent system.
        
        Args:
            query: User query text
            session_id: Optional session ID for context
            
        Returns:
            Response dictionary with content and traces
        """
        start_time = time.time()
        
        try:
            # Get or create session
            if session_id:
                session = await session_manager.get_session(session_id)
                if not session:
                    logger.warning("session_not_found", session_id=session_id)
                    session = await session_manager.create_session()
            else:
                session = await session_manager.create_session()
                
            session_id = session.session_id
            
            # Add user message to session
            await session_manager.add_message(session_id, "user", query)
            
            # Step 1: Orchestrator determines routing
            logger.info("orchestrator_routing", session_id=session_id, query=query)
            await redis_client.publish_agent_event(
                f"session:{session_id}",
                {
                    "type": "agent_started",
                    "agent": "Orchestrator",
                    "module": None,
                    "timestamp": time.time()
                }
            )
            orchestrator_response = await self.orchestrator.execute(
                query=query,
                context=session.context
            )
            await redis_client.publish_agent_event(
                f"session:{session_id}",
                {
                    "type": "agent_completed",
                    "agent": "Orchestrator",
                    "module": orchestrator_response.metadata.get("module_selected"),
                    "timestamp": time.time()
                }
            )
            
            # Extract module from orchestrator response
            module = orchestrator_response.metadata.get("module_selected", "generic")
            await session_manager.set_active_module(session_id, module)
            
            # Step 2: Execute with appropriate executor or team orchestrator
            logger.info("executing_with_module", module=module, session_id=session_id)
            if module == "gis-anomaly":
                await redis_client.publish_agent_event(
                    f"session:{session_id}",
                    {
                        "type": "agent_started",
                        "agent": self.team_orchestrator.name,
                        "module": module,
                        "timestamp": time.time(),
                    },
                )
                executor_response = await self.team_orchestrator.execute(
                    query=query,
                    context={
                        "orchestrator_analysis": orchestrator_response.content,
                        "session_context": session.context,
                        "channel": f"session:{session_id}",
                    },
                )
                await redis_client.publish_agent_event(
                    f"session:{session_id}",
                    {
                        "type": "agent_completed",
                        "agent": self.team_orchestrator.name,
                        "module": module,
                        "timestamp": time.time(),
                    },
                )
            else:
                executor = self.executors.get(module, self.executors["generic"])
                await redis_client.publish_agent_event(
                    f"session:{session_id}",
                    {
                        "type": "agent_started",
                        "agent": executor.name,
                        "module": module,
                        "timestamp": time.time(),
                    },
                )
                executor_response = await executor.execute(
                    query=query,
                    context={
                        "orchestrator_analysis": orchestrator_response.content,
                        "session_context": session.context,
                    },
                )
                await redis_client.publish_agent_event(
                    f"session:{session_id}",
                    {
                        "type": "agent_completed",
                        "agent": executor.name,
                        "module": module,
                        "timestamp": time.time(),
                    },
                )
            
            # Combine traces
            all_traces = orchestrator_response.traces + executor_response.traces
            
            # Update session with assistant response
            await session_manager.add_message(
                session_id,
                "assistant",
                executor_response.content,
                metadata={
                    "module": module,
                    "traces": [t.to_dict() for t in all_traces]
                }
            )
            
            # Publish event to Redis
            await redis_client.publish_agent_event(
                f"session:{session_id}",
                {
                    "type": "query_completed",
                    "session_id": session_id,
                    "module": module,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
            total_duration = (time.time() - start_time) * 1000
            logger.info(
                "query_processed",
                session_id=session_id,
                module=module,
                duration_ms=total_duration
            )
            
            return {
                "session_id": session_id,
                "content": executor_response.content,
                "module": module,
                "traces": [t.to_dict() for t in all_traces],
                "tool_results": executor_response.metadata.get("tool_results", []),
                "duration_ms": total_duration
            }
            
        except Exception as e:
            logger.error("query_processing_failed", error=str(e), query=query)
            raise
            
    async def get_session_history(self, session_id: str) -> dict[str, Any]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data with message history
        """
        session = await session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        return session.to_dict()


agent_service = AgentService()

