from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ApiMetadata(BaseModel):
    name: str
    version: str
    description: str
    endpoints: Dict[str, str]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = Field(default="unknown")


class PrayerTimesResponse(BaseModel):
    timestamp: Optional[datetime] = None
    times: Dict[str, str] = Field(default_factory=dict)


class PlayerStatusResponse(BaseModel):
    is_playing: bool
    last_prayer: Optional[str] = None
    last_file: Optional[str] = None
    volume: int
    muted: bool


class PreviewResponse(BaseModel):
    playing: bool
    prayer: str
    file: Optional[str] = None


class VolumeResponse(BaseModel):
    volume: int


class MuteStateResponse(BaseModel):
    muted: bool


class ReadyResponse(BaseModel):
    status: str
    timestamp: datetime
