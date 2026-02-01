import os
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models.prayer_models import ApiMetadata, HealthResponse, ReadyResponse


router = APIRouter()


@router.get("/", response_model=ApiMetadata, include_in_schema=False)
async def root():
    return ApiMetadata(
        name="al-adhanplayer",
        version=os.getenv("BUILD_ID", "1.0.0"),
        description="Adhan player service with FastAPI and Prometheus metrics.",
        endpoints={
            "health": "/health",
            "ready": "/health/ready",
            "metrics": "/metrics",
        },
    )


@router.api_route("/health", methods=["GET", "HEAD"], response_model=HealthResponse)
async def health(request: Request):
    if request.method == "HEAD":
        return JSONResponse(status_code=200, content=None)
    return HealthResponse(status="healthy", timestamp=datetime.now(), version=os.getenv("BUILD_ID", "unknown"))


@router.api_route("/health/ready", methods=["GET", "HEAD"], response_model=ReadyResponse)
async def ready(request: Request):
    # Simple readiness: app is up and services initialized
    if request.method == "HEAD":
        return JSONResponse(status_code=200, content=None)
    return ReadyResponse(status="ready", timestamp=datetime.now())
