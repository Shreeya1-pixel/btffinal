"""
API route handlers.
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from typing import Any

from backend.api.models import (
    QueryRequest,
    QueryResponse,
    SessionHistoryResponse,
    SessionCreateResponse,
    HealthResponse
)
from backend.services.agent_service import agent_service
from backend.services.session_manager import session_manager
from backend.config import settings
from backend.core.logger import get_logger
from backend import __version__
from backend.core.redis_client import redis_client

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        Application health status
    """
    return HealthResponse(
        status="healthy",
        version=__version__,
        llm_mode=settings.llm_inference_mode
    )


@router.post("/sessions", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session() -> SessionCreateResponse:
    """
    Create a new chat session.
    
    Returns:
        New session information
    """
    try:
        session = await session_manager.create_session()
        return SessionCreateResponse(
            session_id=session.session_id,
            created_at=session.created_at.isoformat()
        )
    except Exception as e:
        logger.error("session_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_session(session_id: str) -> SessionHistoryResponse:
    """
    Get session history and context.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session data with message history
    """
    try:
        history = await agent_service.get_session_history(session_id)
        return SessionHistoryResponse(**history)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("session_retrieval_failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )


@router.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest) -> QueryResponse:
    """
    Process a chat query through the agent system.
    
    Args:
        request: Query request with text and optional session ID
        
    Returns:
        Agent response with traces and tool results
    """
    try:
        result = await agent_service.process_query(
            query=request.query,
            session_id=request.session_id
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.error("chat_processing_failed", error=str(e), query=request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/modules")
async def list_modules() -> dict[str, Any]:
    """
    List available modules and their tools.
    
    Returns:
        Module and tool information
    """
    from backend.tools.base import tool_registry
    
    modules = {}
    for tool in tool_registry.tools.values():
        if tool.module not in modules:
            modules[tool.module] = {
                "name": tool.module,
                "tools": []
            }
        modules[tool.module]["tools"].append({
            "name": tool.name,
            "description": tool.description
        })
        
    return {"modules": list(modules.values())}


@router.get("/events/{session_id}")
async def stream_events(session_id: str):
    """Server-Sent Events stream for agent/trace updates via Redis pub/sub."""
    channel = f"session:{session_id}"

    async def event_generator():
        try:
            async for msg in redis_client.iter_channel(channel):
                yield {"event": "message", "data": msg}
        except asyncio.CancelledError:
            return

    return EventSourceResponse(event_generator())


@router.options("/analyze-stats")
async def analyze_csv_stats_options():
    """Handle OPTIONS preflight for CORS."""
    return {}


@router.post("/analyze-stats")
async def analyze_csv_stats_direct(request: Request):
    """Direct CSV statistics analysis (bypasses LLM for speed)."""
    try:
        body = await request.json()
        csv_data = body.get("csv_data", "")
        
        if not csv_data:
            raise HTTPException(status_code=400, detail="No CSV data provided")
        
        # Import the analyzer function directly
        from backend.tools.csv_analyzer import analyze_csv_stats
        
        # Call the analysis function directly
        result_json = await analyze_csv_stats(csv_data)
        result = json.loads(result_json)
        
        logger.info("csv_analysis_completed", rows=result.get("summary", {}).get("total_rows", 0))
        return result
    except Exception as e:
        logger.error("direct_csv_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomaly/upload")
async def anomaly_upload(
    file: UploadFile = File(...),
    lat_col: str | None = Form(None),
    lon_col: str | None = Form(None),
    value_col: str | None = Form(None),
    top_k: int = Form(10),
    compute_shap: bool = Form(True),
    session_id: str | None = Form(None),
):
    """Upload CSV dataset, convert to GeoJSON, run IsolationForest, and return artifacts."""
    try:
        csv_text = (await file.read()).decode("utf-8", errors="ignore")
        from backend.tools.gis_tools import csv_to_geojson, detect_anomalies_iforest, generate_map_visual

        channel = f"session:{session_id}" if session_id else "dataset"
        await redis_client.publish_agent_event(channel, {"type": "agent_started", "agent": "DatasetIngest", "module": "gis-anomaly"})
        geo = await csv_to_geojson(csv_text=csv_text, lat_col=lat_col, lon_col=lon_col, value_col=value_col)
        await redis_client.publish_agent_event(channel, {"type": "tool_result", "agent": "DatasetIngest", "tool": "csv_to_geojson"})
        anom = await detect_anomalies_iforest(geo_data=geo, top_k=top_k, return_shap=compute_shap)
        await redis_client.publish_agent_event(channel, {"type": "tool_result", "agent": "DatasetIngest", "tool": "detect_anomalies_iforest"})
        vis = await generate_map_visual(geo_data=geo, anomalies=anom)
        await redis_client.publish_agent_event(channel, {"type": "tool_result", "agent": "DatasetIngest", "tool": "generate_map_visual"})
        await redis_client.publish_agent_event(channel, {"type": "agent_completed", "agent": "DatasetIngest", "module": "gis-anomaly"})
        return {"geojson": geo, "anomalies": anom, "map": vis}
    except Exception as e:
        logger.error("anomaly_upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

