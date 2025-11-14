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
        error_str = str(e)
        logger.error("chat_processing_failed", error=error_str, query=request.query)
        
        # Provide user-friendly error messages
        if "quota" in error_str.lower() or "429" in error_str or "insufficient_quota" in error_str:
            detail = "API Quota Exceeded: Your OpenAI API key has exceeded its quota. Please check your billing at https://platform.openai.com/account/billing"
            status_code = status.HTTP_402_PAYMENT_REQUIRED
        elif "401" in error_str or "invalid" in error_str.lower() and "api key" in error_str.lower():
            detail = "Invalid API Key: Please check your OpenAI API key configuration."
            status_code = status.HTTP_401_UNAUTHORIZED
        elif "model" in error_str.lower() and ("not found" in error_str.lower() or "does not exist" in error_str.lower()):
            detail = f"Model Error: {error_str}"
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            detail = f"Failed to process query: {error_str}"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail=detail
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


@router.post("/life-manager/email/send")
async def send_email_endpoint(request: Request):
    """Send an email via the life manager."""
    try:
        body = await request.json()
        from backend.tools.life_manager_tools import send_email
        
        result_json = await send_email(
            to=body.get("to"),
            subject=body.get("subject"),
            body=body.get("body"),
            cc=body.get("cc"),
            bcc=body.get("bcc"),
            smtp_server=body.get("smtp_server"),
            smtp_port=body.get("smtp_port"),
            username=body.get("username"),
            password=body.get("password")
        )
        result = json.loads(result_json)
        return result
    except Exception as e:
        logger.error("email_send_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/life-manager/schedule")
async def schedule_event_endpoint(request: Request):
    """Schedule an event."""
    try:
        body = await request.json()
        from backend.tools.life_manager_tools import schedule_event
        
        result_json = await schedule_event(
            title=body.get("title"),
            start_time=body.get("start_time"),
            duration_minutes=body.get("duration_minutes", 60),
            description=body.get("description"),
            location=body.get("location"),
            attendees=body.get("attendees")
        )
        result = json.loads(result_json)
        return result
    except Exception as e:
        logger.error("schedule_event_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/life-manager/task")
async def create_task_endpoint(request: Request):
    """Create a task."""
    try:
        body = await request.json()
        from backend.tools.life_manager_tools import create_task
        
        result_json = await create_task(
            title=body.get("title"),
            description=body.get("description"),
            due_date=body.get("due_date"),
            priority=body.get("priority", "medium"),
            status=body.get("status", "todo")
        )
        result = json.loads(result_json)
        return result
    except Exception as e:
        logger.error("create_task_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/life-manager/whatsapp/send")
async def send_whatsapp_endpoint(request: Request):
    """Sends a WhatsApp message after user approval."""
    try:
        body = await request.json()
        from backend.tools.life_manager_tools import send_whatsapp_message
        
        result_json = await send_whatsapp_message(
            phone_number=body.get("phone_number"),
            message=body.get("message")
        )
        result = json.loads(result_json)
        return result
    except Exception as e:
        logger.error("whatsapp_send_endpoint_failed", error=str(e))
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

