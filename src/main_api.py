"""
Main FastAPI application for Gemini File Analysis with SURA Healthcare integration.

This application provides:
- General file analysis endpoints (existing functionality)
- SURA Healthcare eligibility analysis endpoints (new)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.client_manager import ClientManager
from src.api.sura.routes import router as sura_router
from src.api.sura.summarizer_routes import summarizer_router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.

    Handles startup and shutdown tasks, including client initialization
    and resource cleanup.
    """
    # Startup
    logger.info("Starting Gemini File Analysis API with SURA Healthcare integration...")
    client_manager = ClientManager.get_instance()

    # Pre-initialize client to establish connections
    try:
        client = client_manager.get_client()
        logger.info(
            f"Successfully initialized Gemini client with model: {client.model_name}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize client on startup: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Gemini File Analysis API...")
    client_manager.shutdown()


# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="Gemini File Analysis API with SURA Healthcare",
    description=(
        "Multi-format file analysis with streaming support via SAP BTP GenAI Hub. "
        "Includes SURA Healthcare eligibility auditing for medical records."
    ),
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register SURA routes
app.include_router(sura_router)
app.include_router(summarizer_router)

logger.info("SURA Healthcare routes registered at /api/v1/sura")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Gemini File Analysis API with SURA Healthcare",
        "version": "1.0.0",
        "endpoints": {
            "sura_contracts": "/api/v1/sura/contracts",
            "sura_analyze": "/api/v1/sura/analyze-eligibility",
            "sura_summarize": "/api/v1/sura/summarize-clinical",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        client_manager = ClientManager.get_instance()
        client = client_manager.get_client()
        client_healthy = client.is_healthy()

        print(client)

        return {
            "status": "healthy" if client_healthy else "degraded",
            "model": client.model_name,
            "client_healthy": client_healthy,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
