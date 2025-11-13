"""
Session management for maintaining conversation context and state.
"""

from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

from backend.core.redis_client import redis_client
from backend.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Message:
    """Chat message in a session."""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Session:
    """User session with conversation history and context."""
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    messages: list[Message] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    active_module: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "context": self.context,
            "active_module": self.active_module
        }


class SessionManager:
    """Manage user sessions and conversation history."""
    
    def __init__(self):
        self.sessions: dict[str, Session] = {}
        
    async def create_session(self) -> Session:
        """
        Create a new session.
        
        Returns:
            New Session instance
        """
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id)
        
        self.sessions[session_id] = session
        await redis_client.set_session(session_id, session.to_dict())
        
        logger.info("session_created", session_id=session_id)
        return session
        
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session or None if not found
        """
        # Check in-memory cache first
        if session_id in self.sessions:
            return self.sessions[session_id]
            
        # Try Redis
        session_data = await redis_client.get_session(session_id)
        if session_data:
            session = self._deserialize_session(session_data)
            self.sessions[session_id] = session
            return session
            
        return None
        
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Add a message to session.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.updated_at = datetime.utcnow()
        
        await redis_client.set_session(session_id, session.to_dict())
        logger.debug("message_added", session_id=session_id, role=role)
        
    async def update_context(
        self, 
        session_id: str, 
        context_updates: dict[str, Any]
    ) -> None:
        """
        Update session context.
        
        Args:
            session_id: Session identifier
            context_updates: Context fields to update
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        session.context.update(context_updates)
        session.updated_at = datetime.utcnow()
        
        await redis_client.set_session(session_id, session.to_dict())
        logger.debug("context_updated", session_id=session_id)
        
    async def set_active_module(self, session_id: str, module: str) -> None:
        """
        Set the active module for the session.
        
        Args:
            session_id: Session identifier
            module: Module name
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        session.active_module = module
        session.updated_at = datetime.utcnow()
        
        await redis_client.set_session(session_id, session.to_dict())
        logger.debug("active_module_set", session_id=session_id, module=module)
        
    def _deserialize_session(self, data: dict[str, Any]) -> Session:
        """Deserialize session from dictionary."""
        messages = [
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
                metadata=msg.get("metadata", {})
            )
            for msg in data["messages"]
        ]
        
        return Session(
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=messages,
            context=data["context"],
            active_module=data.get("active_module")
        )


session_manager = SessionManager()

