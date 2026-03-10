"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint."""
    return {"ready": True, "checks": {"model_loaded": True}}
