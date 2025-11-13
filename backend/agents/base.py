"""
Base agent functionality and orchestration.
"""

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from backend.core.logger import get_logger

logger = get_logger(__name__)


class AgentRole(str, Enum):
    """Agent roles in the system."""
    ORCHESTRATOR = "orchestrator"
    QUERY_INTERPRETER = "query_interpreter"
    TOOL_EXECUTOR = "tool_executor"
    EXPLAINER = "explainer"


@dataclass
class AgentTrace:
    """Trace information for agent execution."""
    agent_name: str
    role: AgentRole
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tools_called: list[str] = field(default_factory=list)
    handoffs: list[str] = field(default_factory=list)
    duration_ms: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "agent_name": self.agent_name,
            "role": self.role.value,
            "timestamp": self.timestamp.isoformat(),
            "tools_called": self.tools_called,
            "handoffs": self.handoffs,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }


@dataclass
class AgentResponse:
    """Response from agent execution."""
    content: str
    traces: list[AgentTrace]
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "traces": [trace.to_dict() for trace in self.traces],
            "metadata": self.metadata,
            "session_id": self.session_id
        }


class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, role: AgentRole, instructions: str):
        """
        Initialize agent.
        
        Args:
            name: Agent name
            role: Agent role
            instructions: System instructions for the agent
        """
        self.name = name
        self.role = role
        self.instructions = instructions
        self.traces: list[AgentTrace] = []
        logger.info("agent_initialized", name=name, role=role.value)
        
    def create_trace(self) -> AgentTrace:
        """
        Create a new trace for this agent.
        
        Returns:
            New AgentTrace instance
        """
        trace = AgentTrace(agent_name=self.name, role=self.role)
        self.traces.append(trace)
        return trace
        
    async def execute(
        self, 
        query: str, 
        context: Optional[dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute agent logic.
        
        Args:
            query: User query
            context: Optional context from previous agents
            
        Returns:
            AgentResponse with results
        """
        raise NotImplementedError("Subclasses must implement execute()")

