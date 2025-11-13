"""
Pydantic models for API requests and responses.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for chat queries."""
    query: str = Field(..., description="User query text", min_length=1)
    session_id: Optional[str] = Field(None, description="Optional session ID")


class TraceInfo(BaseModel):
    """Agent trace information."""
    agent_name: str
    role: str
    timestamp: str
    tools_called: list[str]
    handoffs: list[str]
    duration_ms: Optional[float]
    metadata: dict[str, Any]


class ToolResult(BaseModel):
    """Tool execution result."""
    tool: str
    args: dict[str, Any]
    result: str


class QueryResponse(BaseModel):
    """Response model for chat queries."""
    session_id: str
    content: str
    module: str
    traces: list[TraceInfo]
    tool_results: list[ToolResult]
    duration_ms: float


class SessionHistoryResponse(BaseModel):
    """Response model for session history."""
    session_id: str
    created_at: str
    updated_at: str
    messages: list[dict[str, Any]]
    context: dict[str, Any]
    active_module: Optional[str]


class SessionCreateResponse(BaseModel):
    """Response model for session creation."""
    session_id: str
    created_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    llm_mode: str

