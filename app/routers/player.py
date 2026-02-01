from fastapi import APIRouter, Request, HTTPException, Query
from app.models.prayer_models import (
    PlayerStatusResponse,
    PreviewResponse,
    VolumeResponse,
    MuteStateResponse,
)

router = APIRouter(prefix="/api/v1/player", tags=["player"])

ALLOWED_PRAYERS = {"fajr", "dhuhr", "asr", "maghrib", "isha"}


@router.get("/status", response_model=PlayerStatusResponse)
async def status(request: Request):
    svc = request.app.state.player_service
    return svc.status()


@router.post("/preview", response_model=PreviewResponse)
async def preview(request: Request, prayer: str = Query(..., description="Prayer name")):
    if prayer.lower() not in ALLOWED_PRAYERS:
        raise HTTPException(status_code=400, detail="Invalid prayer. Use fajr|dhuhr|asr|maghrib|isha")
    svc = request.app.state.player_service
    file_path = svc.preview(prayer)
    if not file_path:
        raise HTTPException(status_code=404, detail="No media file available")
    return {"playing": True, "prayer": prayer, "file": file_path}


@router.post("/volume", response_model=VolumeResponse)
async def set_volume(request: Request, level: int = Query(..., ge=0, le=100)):
    svc = request.app.state.player_service
    new_level = svc.set_volume(level)
    return {"volume": new_level}


@router.post("/mute", response_model=MuteStateResponse)
async def mute(request: Request):
    svc = request.app.state.player_service
    svc.mute()
    return {"muted": True}


@router.post("/unmute", response_model=MuteStateResponse)
async def unmute(request: Request):
    svc = request.app.state.player_service
    svc.unmute()
    return {"muted": False}
