from fastapi import APIRouter
from datetime import datetime, timezone
from app.core.config import settings

router = APIRouter()

@router.get("/health", summary="System Health Check")
async def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": "healthy",
            "database": "not_configured",
            "redis": "not_configured"
        }
    }
