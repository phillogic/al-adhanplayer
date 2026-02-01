from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class MediaItem(BaseModel):
    kind: Literal["file", "dir"]
    name: str
    rel_path: str = Field(description="Path relative to MEDIA_DIR")
    size_bytes: int = 0
    modified_at: Optional[datetime] = None
    extension: Optional[str] = None


class MediaListResponse(BaseModel):
    base_path: str
    rel_path: str
    recursive: bool = False
    include_hidden: bool = False
    items: List[MediaItem]


class MediaStats(BaseModel):
    total_files: int
    total_size_bytes: int
    fajr_files: int
    fajr_size_bytes: int
    other_files: int
    other_size_bytes: int


class MediaUploadResponse(BaseModel):
    base_path: str
    rel_dest: str
    saved: List[MediaItem]
    skipped: List[str] = Field(default_factory=list)
    message: Optional[str] = None


class MediaDeleteResponse(BaseModel):
    rel_path: str
    deleted: bool
    message: Optional[str] = None
