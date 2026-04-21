import os
import re
import uuid

import requests as req_lib
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import COVERS_DIR, MUSIC_DIR
from app.database import get_db
from app.models.music import Music
from app.schemas.online import (
    OnlineLyricResponse,
    OnlinePicResponse,
    OnlineSearchResponse,
    OnlineSearchResult,
    OnlineUrlResponse,
    UnifiedSearchResponse,
)

router = APIRouter()

TONZHON_API = "https://tonzhon.com/api.php"
TONZHON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://tonzhon.com/",
    "Accept": "*/*",
}

_session = req_lib.Session()
_session.headers.update(TONZHON_HEADERS)


def _parse_artist_str(artist_data) -> str:
    if isinstance(artist_data, list):
        if len(artist_data) > 0 and isinstance(artist_data[0], list):
            return "/".join([a[0] for a in artist_data if a])
        elif len(artist_data) > 0:
            return "/".join(str(a) for a in artist_data)
    return str(artist_data) if artist_data else "未知艺术家"


def _music_to_unified(music: Music) -> dict:
    return {
        "source": "library",
        "id": str(music.id),
        "name": music.title,
        "artist": music.artist,
        "album": music.album or "",
        "duration": music.duration,
        "format": music.format,
        "has_cover": bool(music.cover_path),
        "stream_url": f"/api/musics/{music.id}/stream",
        "cover_url": f"/api/musics/{music.id}/cover" if music.cover_path else None,
    }


@router.get("/unified-search", response_model=UnifiedSearchResponse)
def unified_search(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    db: Session = Depends(get_db),
):
    library_results = _search_library(keyword, db)
    online_results = _search_online(keyword)

    return UnifiedSearchResponse(
        library=library_results,
        online=online_results,
    )


def _search_library(keyword: str, db: Session) -> list[dict]:
    safe_search = re.sub(r"[_%\\]", r"\\\g<0>", keyword)
    pattern = f"%{safe_search}%"
    musics = (
        db.query(Music)
        .filter(
            or_(
                Music.title.ilike(pattern),
                Music.artist.ilike(pattern),
                Music.album.ilike(pattern),
            )
        )
        .order_by(Music.created_at.desc())
        .limit(30)
        .all()
    )
    return [_music_to_unified(m) for m in musics]


def _search_online(keyword: str) -> list[dict]:
    try:
        resp = _session.get(
            TONZHON_API,
            params={
                "types": "search",
                "count": 20,
                "source": "netease",
                "pages": 1,
                "name": keyword,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        artist = _parse_artist_str(item.get("artist", []))
        results.append({
            "source": "online",
            "id": str(item.get("id", "")),
            "name": item.get("name", ""),
            "artist": artist,
            "album": item.get("album", ""),
            "url_id": str(item.get("url_id", "")),
            "pic_id": str(item.get("pic_id", "")),
            "lyric_id": str(item.get("lyric_id", "")),
        })
    return results


@router.post("/import")
def import_online_song(
    id: str = Query(..., description="在线歌曲ID"),
    source: str = Query("netease", description="音乐源"),
    name: str = Query("", description="歌曲名"),
    artist: str = Query("", description="歌手"),
    album: str = Query("", description="专辑"),
    db: Session = Depends(get_db),
):
    song_url = _get_song_url_str(id, source)
    if not song_url:
        raise HTTPException(status_code=404, detail="无法获取歌曲下载链接")

    try:
        resp = req_lib.get(song_url, headers=TONZHON_HEADERS, timeout=60)
        resp.raise_for_status()
        audio_data = resp.content
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"下载歌曲失败: {e}")

    safe_name = re.sub(r'[^\w\s\-.]', '_', name or id)
    filename = f"{uuid.uuid4().hex}.mp3"
    file_path = os.path.join(MUSIC_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(audio_data)

    cover_path = None
    pic_id = ""
    try:
        pic_resp = _session.get(
            TONZHON_API,
            params={"types": "pic", "id": id, "source": source},
            timeout=10,
        )
        pic_data = pic_resp.json()
        pic_url = pic_data.get("url", "")
        if pic_url:
            pic_download = req_lib.get(pic_url, headers=TONZHON_HEADERS, timeout=15)
            if pic_download.status_code == 200 and len(pic_download.content) > 100:
                cover_filename = f"{uuid.uuid4().hex}.jpg"
                cover_path = os.path.join(COVERS_DIR, cover_filename)
                with open(cover_path, "wb") as f:
                    f.write(pic_download.content)
    except Exception:
        pass

    duration = 0
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(file_path)
        if audio and hasattr(audio, "info"):
            duration = int(getattr(audio.info, "length", 0) or 0)
    except Exception:
        pass

    music = Music(
        title=name or "未知歌曲",
        artist=artist or "未知艺术家",
        album=album or "未知专辑",
        file_path=file_path,
        cover_path=cover_path,
        duration=duration,
        file_size=len(audio_data),
        format="mp3",
    )
    db.add(music)
    db.commit()
    db.refresh(music)

    return {
        "imported": True,
        "music": {
            "id": music.id,
            "title": music.title,
            "artist": music.artist,
            "album": music.album,
            "duration": music.duration,
            "stream_url": f"/api/musics/{music.id}/stream",
            "cover_url": f"/api/musics/{music.id}/cover" if music.cover_path else None,
        },
    }


@router.get("/search", response_model=OnlineSearchResponse)
def search_songs(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    source: str = Query("netease", description="音乐源: netease"),
    count: int = Query(20, ge=1, le=50, description="返回数量"),
    page: int = Query(1, ge=1, description="页码"),
):
    try:
        resp = _session.get(
            TONZHON_API,
            params={
                "types": "search",
                "count": count,
                "source": source,
                "pages": page,
                "name": keyword,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"搜索请求失败: {e}")

    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="搜索返回数据格式异常")

    items = []
    for item in data:
        items.append(
            OnlineSearchResult(
                id=str(item.get("id", "")),
                name=item.get("name", ""),
                artist=item.get("artist", []),
                album=item.get("album", ""),
                source=item.get("source", source),
                url_id=str(item.get("url_id", "")),
                pic_id=str(item.get("pic_id", "")),
                lyric_id=str(item.get("lyric_id", "")),
            )
        )

    return OnlineSearchResponse(total=len(items), items=items)


def _get_song_url_str(song_id: str, source: str) -> str:
    try:
        resp = _session.get(
            TONZHON_API,
            params={"types": "url", "id": song_id, "source": source},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return ""

    url = data.get("url", "")
    if not url and source == "netease":
        url = f"https://music.163.com/song/media/outer/url?id={song_id}.mp3"
    return url


@router.get("/url", response_model=OnlineUrlResponse)
def get_song_url(
    id: str = Query(..., description="歌曲ID"),
    source: str = Query("netease", description="音乐源"),
):
    url = _get_song_url_str(id, source)
    if not url:
        raise HTTPException(status_code=502, detail="获取歌曲链接失败")
    return OnlineUrlResponse(url=url)


@router.get("/lyric", response_model=OnlineLyricResponse)
def get_lyric(
    id: str = Query(..., description="歌词ID"),
    source: str = Query("netease", description="音乐源"),
):
    try:
        resp = _session.get(
            TONZHON_API,
            params={"types": "lyric", "id": id, "source": source},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取歌词失败: {e}")

    return OnlineLyricResponse(lyric=data.get("lyric", ""))


@router.get("/pic", response_model=OnlinePicResponse)
def get_pic(
    id: str = Query(..., description="封面ID"),
    source: str = Query("netease", description="音乐源"),
):
    try:
        resp = _session.get(
            TONZHON_API,
            params={"types": "pic", "id": id, "source": source},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取封面失败: {e}")

    return OnlinePicResponse(url=data.get("url", ""))


@router.get("/download")
def download_song(
    id: str = Query(..., description="歌曲ID"),
    source: str = Query("netease", description="音乐源"),
    name: str = Query("", description="文件名"),
):
    song_url = _get_song_url_str(id, source)
    if not song_url:
        raise HTTPException(status_code=404, detail="无法获取歌曲下载链接")

    try:
        stream_resp = req_lib.get(
            song_url,
            headers=TONZHON_HEADERS,
            stream=True,
            timeout=30,
        )
        stream_resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"下载歌曲失败: {e}")

    filename = f"{name}.mp3" if name else f"{id}.mp3"
    content_type = stream_resp.headers.get("content-type", "audio/mpeg")

    def iter_content():
        for chunk in stream_resp.iter_content(chunk_size=65536):
            if chunk:
                yield chunk

    return StreamingResponse(
        iter_content(),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
