from fastapi import APIRouter, Request
from app.models.prayer_models import PrayerTimesResponse

router = APIRouter(prefix="/api/v1/prayer", tags=["prayer"])


@router.get("/times", response_model=PrayerTimesResponse)
async def get_times(request: Request):
    svc = request.app.state.prayer_service
    return svc.times_response()


@router.post("/refresh", response_model=PrayerTimesResponse)
async def refresh_times(request: Request):
    svc = request.app.state.prayer_service
    ts, times, _ = svc.refresh_times()
    return {"timestamp": ts, "times": times}
