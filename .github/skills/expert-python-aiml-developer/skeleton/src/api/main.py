"""FastAPI application for model serving."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_api_settings
from src.api.routes import health, predictions

logger = logging.getLogger(__name__)
settings = get_api_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting application...")
    # Load model here
    # app.state.model = load_model()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="ML Model API",
    description="Production ML Model Inference API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {"name": "ML Model API", "version": "1.0.0", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
