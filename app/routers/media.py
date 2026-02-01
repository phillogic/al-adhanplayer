import os
import mimetypes
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, File, status
from fastapi.responses import FileResponse

from app.models.media_models import (
    MediaItem,
    MediaListResponse,
    MediaStats,
    MediaUploadResponse,
    MediaDeleteResponse,
)


router = APIRouter(prefix="/api/v1/media", tags=["media"])


def _resolve_media_paths(request: Request) -> tuple[str, str]:
    base = os.path.abspath(os.getenv("MEDIA_DIR", "media"))
    fajr_subdir = os.path.abspath(os.getenv("FAJR_SUBDIR", os.path.join(base, "fajr")))
    return base, fajr_subdir


def _safe_join(base: str, rel_path: str) -> str:
    # Normalize and prevent path traversal outside base
    candidate = os.path.abspath(os.path.join(base, rel_path or ""))
    if not candidate.startswith(base):
        raise ValueError("Invalid path: outside media directory")
    return candidate


def _list_dir(path: str, recursive: bool, include_hidden: bool) -> List[MediaItem]:
    items: List[MediaItem] = []
    base_len = len(path.rstrip(os.sep)) + 1

    def add_file(fp: str):
        st = os.stat(fp)
        name = os.path.basename(fp)
        if not include_hidden and name.startswith('.'):
            return
        items.append(
            MediaItem(
                kind="file",
                name=name,
                rel_path=fp[base_len:],
                size_bytes=st.st_size,
                modified_at=datetime.fromtimestamp(st.st_mtime),
                extension=os.path.splitext(name)[1].lstrip('.').lower() or None,
            )
        )

    def add_dir(dp: str):
        name = os.path.basename(dp)
        if not include_hidden and name.startswith('.'):
            return
        items.append(
            MediaItem(
                kind="dir",
                name=name,
                rel_path=dp[base_len:],
            )
        )

    if recursive:
        for root, dirs, files in os.walk(path, topdown=True):
            # Optionally filter hidden directories
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            # Add current dir (skip base itself)
            if root != path:
                add_dir(root)
            for f in files:
                add_file(os.path.join(root, f))
    else:
        if not os.path.isdir(path):
            raise FileNotFoundError(path)
        # one level scan
        with os.scandir(path) as it:
            for entry in it:
                if not include_hidden and entry.name.startswith('.'):
                    continue
                full = entry.path
                if entry.is_dir(follow_symlinks=False):
                    add_dir(full)
                elif entry.is_file(follow_symlinks=False):
                    add_file(full)
    # stable order: dirs first then files by name
    items.sort(key=lambda x: (0 if x.kind == "dir" else 1, x.name.lower()))
    return items


@router.get("/list", response_model=MediaListResponse)
def list_media(
    request: Request,
    path: Optional[str] = Query(None, description="Relative path under MEDIA_DIR to list"),
    recursive: bool = Query(False),
    include_hidden: bool = Query(False),
):
    base, _ = _resolve_media_paths(request)
    try:
        target = _safe_join(base, path or "")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        items = _list_dir(target, recursive=recursive, include_hidden=include_hidden)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Path not found")

    rel = os.path.relpath(target, base) if target != base else ""
    return MediaListResponse(
        base_path=base,
        rel_path=rel,
        recursive=recursive,
        include_hidden=include_hidden,
        items=items,
    )


@router.get("/stats", response_model=MediaStats)
def media_stats(request: Request):
    base, fajr_dir = _resolve_media_paths(request)
    total_files = 0
    total_size = 0
    fajr_files = 0
    fajr_size = 0

    for root, _, files in os.walk(base, topdown=True):
        for f in files:
            fp = os.path.join(root, f)
            try:
                st = os.stat(fp)
            except FileNotFoundError:
                continue
            total_files += 1
            total_size += st.st_size
            if os.path.abspath(root).startswith(fajr_dir):
                fajr_files += 1
                fajr_size += st.st_size

    return MediaStats(
        total_files=total_files,
        total_size_bytes=total_size,
        fajr_files=fajr_files,
        fajr_size_bytes=fajr_size,
        other_files=total_files - fajr_files,
        other_size_bytes=total_size - fajr_size,
    )


@router.get("/file", response_model=MediaItem)
def file_info(request: Request, rel_path: str = Query(..., description="File path relative to MEDIA_DIR")):
    base, _ = _resolve_media_paths(request)
    try:
        target = _safe_join(base, rel_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")
    st = os.stat(target)
    name = os.path.basename(target)
    return MediaItem(
        kind="file",
        name=name,
        rel_path=rel_path,
        size_bytes=st.st_size,
        modified_at=datetime.fromtimestamp(st.st_mtime),
        extension=os.path.splitext(name)[1].lstrip('.').lower() or None,
    )


@router.get(
    "/download",
    responses={
        200: {
            "content": {
                "application/octet-stream": {"schema": {"type": "string", "format": "binary"}},
                "audio/mpeg": {"schema": {"type": "string", "format": "binary"}},
            },
            "description": "Binary file download",
        }
    },
)
def download_file(request: Request, rel_path: str = Query(..., description="File path relative to MEDIA_DIR")):
    base, _ = _resolve_media_paths(request)
    try:
        target = _safe_join(base, rel_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")

    filename = os.path.basename(target)
    mime, _ = mimetypes.guess_type(filename)
    media_type = mime or "application/octet-stream"
    # FileResponse sets Content-Disposition with filename to prompt download in browsers
    return FileResponse(path=target, media_type=media_type, filename=filename)


@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    request: Request,
    files: list[UploadFile] = File(..., description="One or more files to upload"),
    dest: str = Query("", description="Destination relative folder under MEDIA_DIR (optional)"),
):
    base, _ = _resolve_media_paths(request)
    # Validate destination path
    try:
        dest_abs = _safe_join(base, dest)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid destination path")
    os.makedirs(dest_abs, exist_ok=True)

    allowed_ext = {".mp3"}
    saved: list[MediaItem] = []
    skipped: list[str] = []

    for f in files:
        name = os.path.basename(f.filename or "")
        if not name:
            skipped.append("<unnamed>")
            continue
        ext = os.path.splitext(name)[1].lower()
        if allowed_ext and ext not in allowed_ext:
            skipped.append(name)
            continue
        target = os.path.join(dest_abs, name)
        # Save to disk
        try:
            with open(target, "wb") as out:
                while True:
                    chunk = await f.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            st = os.stat(target)
            rel_saved = os.path.relpath(target, base)
            saved.append(
                MediaItem(
                    kind="file",
                    name=name,
                    rel_path=rel_saved,
                    size_bytes=st.st_size,
                    modified_at=datetime.fromtimestamp(st.st_mtime),
                    extension=ext.lstrip('.') or None,
                )
            )
        finally:
            await f.close()

    rel_dest = os.path.relpath(dest_abs, base) if dest_abs != base else ""
    return MediaUploadResponse(
        base_path=base,
        rel_dest=rel_dest,
        saved=saved,
        skipped=skipped,
        message=f"Saved {len(saved)} file(s), skipped {len(skipped)}",
    )


@router.delete("/file", response_model=MediaDeleteResponse)
def delete_file(request: Request, rel_path: str = Query(..., description="File path relative to MEDIA_DIR to delete")):
    base, _ = _resolve_media_paths(request)
    try:
        target = _safe_join(base, rel_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="Path not found")
    if os.path.isdir(target):
        raise HTTPException(status_code=400, detail="Refusing to delete directories via this endpoint")
    try:
        os.remove(target)
        return MediaDeleteResponse(rel_path=rel_path, deleted=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")
