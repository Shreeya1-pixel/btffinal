"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.core.logger import configure_logging, get_logger
from backend.core.redis_client import redis_client
from backend.api.routes import router
from backend import __version__

# Import tools to register them
from backend.tools import generic_tools, gis_tools, csv_analyzer

configure_logging(settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("application_starting", version=__version__)
    
    try:
        await redis_client.connect()
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        
    logger.info(
        "application_ready",
        host=settings.app_host,
        port=settings.app_port,
        llm_mode=settings.llm_inference_mode
    )
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    await redis_client.disconnect()
    logger.info("application_stopped")


app = FastAPI(
    title="Neuroverse AI",
    description="Agent-driven platform for natural language queries and GIS analytics",
    version=__version__,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Neuroverse AI",
        "version": __version__,
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )

