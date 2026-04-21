import os
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.auth import get_admin_user, get_current_user
from app.config import ALLOWED_AUDIO_EXTENSIONS, UPLOAD_MAX_SIZE_MB
from app.database import get_db
from app.models.music import Music
from app.models.tag import Tag
from app.models.user import User
from app.schemas.music import MusicListOut, MusicOut, MusicUpdate
from app.utils.file_handler import (
    delete_cover_file,
    delete_music_file,
    extract_cover,
    extract_metadata,
    generate_safe_filename,
    save_upload_file,
    validate_audio_extension,
)

router = APIRouter()


def _music_to_out(music: Music) -> dict:
    return {
        "id": music.id,
        "title": music.title,
        "artist": music.artist,
        "album": music.album,
        "duration": music.duration,
        "file_size": music.file_size,
        "format": music.format,
        "has_cover": bool(music.cover_path),
        "created_at": music.created_at,
        "uploader_id": music.uploader_id,
        "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in music.tags],
        "stream_url": f"/api/musics/{music.id}/stream",
        "download_url": f"/api/musics/{music.id}/download",
        "cover_url": f"/api/musics/{music.id}/cover" if music.cover_path else None,
    }


@router.post("/", response_model=MusicOut, status_code=status.HTTP_201_CREATED)
def upload_music(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件名不能为空")

    if not validate_audio_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的音频格式，允许: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}",
        )

    safe_name = generate_safe_filename(file.filename)
    file_path = save_upload_file(file, safe_name)

    max_bytes = UPLOAD_MAX_SIZE_MB * 1024 * 1024
    actual_size = os.path.getsize(file_path)
    if actual_size > max_bytes:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制（{UPLOAD_MAX_SIZE_MB}MB）",
        )

    metadata = extract_metadata(file_path, file.filename)
    cover_path = extract_cover(file_path)

    music = Music(
        title=metadata["title"],
        artist=metadata["artist"],
        album=metadata["album"],
        file_path=file_path,
        cover_path=cover_path,
        duration=metadata["duration"],
        file_size=metadata["file_size"],
        format=metadata["format"],
        uploader_id=current_user.id,
    )
    db.add(music)
    db.commit()
    db.refresh(music)
    return _music_to_out(music)


@router.get("/", response_model=MusicListOut)
def list_musics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Music)

    if search:
        safe_search = re.sub(r"[_%\\]", r"\\\g<0>", search)
        pattern = f"%{safe_search}%"
        query = query.filter(
            or_(
                Music.title.ilike(pattern),
                Music.artist.ilike(pattern),
                Music.album.ilike(pattern),
            )
        )

    if tag:
        tag_obj = db.query(Tag).filter(Tag.name == tag).first()
        if tag_obj:
            query = query.filter(Music.tags.contains(tag_obj))

    total = query.count()
    items = query.order_by(Music.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return MusicListOut(total=total, items=[_music_to_out(m) for m in items])


@router.get("/{music_id}", response_model=MusicOut)
def get_music(music_id: int, db: Session = Depends(get_db)):
    music = db.query(Music).filter(Music.id == music_id).first()
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音乐不存在")
    return _music_to_out(music)


@router.put("/{music_id}", response_model=MusicOut)
def update_music(
    music_id: int,
    data: MusicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    music = db.query(Music).filter(Music.id == music_id).first()
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音乐不存在")

    update_data = data.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for key, value in update_data.items():
        setattr(music, key, value)

    if tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        music.tags = tags

    db.commit()
    db.refresh(music)
    return _music_to_out(music)


@router.delete("/{music_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_music(
    music_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    music = db.query(Music).filter(Music.id == music_id).first()
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音乐不存在")

    delete_music_file(music.file_path)
    delete_cover_file(music.cover_path)
    db.delete(music)
    db.commit()


@router.get("/{music_id}/stream")
def stream_music(music_id: int, request: Request, db: Session = Depends(get_db)):
    music = db.query(Music).filter(Music.id == music_id).first()
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音乐不存在")

    if not os.path.exists(music.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音频文件不存在")

    file_size = os.path.getsize(music.file_path)
    content_type = _get_content_type(music.format)

    range_header = request.headers.get("range")
    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            end = min(end, file_size - 1)

            if start >= file_size:
                return StreamingResponse(
                    status_code=416,
                    headers={"Content-Range": f"bytes */{file_size}"},
                )

            content_length = end - start + 1

            def iter_range():
                with open(music.file_path, "rb") as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(64 * 1024, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            safe_title = re.sub(r'[^\w\s\-.]', '', music.title)
            return StreamingResponse(
                iter_range(),
                status_code=206,
                media_type=content_type,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(content_length),
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": f"inline; filename=\"{safe_title}.{music.format}\"",
                },
            )

    def iter_file():
        with open(music.file_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                yield chunk

    safe_title = re.sub(r'[^\w\s\-.]', '', music.title)
    return StreamingResponse(
        iter_file(),
        media_type=content_type,
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Content-Disposition": f"inline; filename=\"{safe_title}.{music.format}\"",
        },
    )


@router.get("/{music_id}/download")
def download_music(
    music_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    music = db.query(Music).filter(Music.id == music_id).first()
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音乐不存在")

    if not os.path.exists(music.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音频文件不存在")

    safe_title = re.sub(r'[^\w\s\-.]', '', music.title)
    filename = f"{safe_title}.{music.format}"
    return FileResponse(
        path=music.file_path,
        filename=filename,
        media_type=_get_content_type(music.format),
    )


@router.get("/{music_id}/cover")
def get_music_cover(music_id: int, db: Session = Depends(get_db)):
    music = db.query(Music).filter(Music.id == music_id).first()
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音乐不存在")

    if not music.cover_path or not os.path.exists(music.cover_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="封面不存在")

    return FileResponse(path=music.cover_path, media_type="image/jpeg")


def _get_content_type(fmt: str) -> str:
    mapping = {
        "mp3": "audio/mpeg",
        "flac": "audio/flac",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "aac": "audio/aac",
        "m4a": "audio/mp4",
    }
    return mapping.get(fmt.lower(), "application/octet-stream")
