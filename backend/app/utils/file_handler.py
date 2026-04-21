import os
import uuid

from mutagen import File as MutagenFile

from app.config import ALLOWED_AUDIO_EXTENSIONS, COVERS_DIR, MUSIC_DIR

CHUNK_SIZE = 64 * 1024


def validate_audio_extension(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_AUDIO_EXTENSIONS


def generate_safe_filename(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def save_upload_file(upload_file, filename: str) -> str:
    file_path = os.path.join(MUSIC_DIR, filename)
    with open(file_path, "wb") as f:
        while chunk := upload_file.file.read(CHUNK_SIZE):
            f.write(chunk)
    return file_path


def extract_metadata(file_path: str, original_filename: str) -> dict:
    ext = os.path.splitext(original_filename)[1].lower().lstrip(".")
    file_size = os.path.getsize(file_path)

    title = os.path.splitext(original_filename)[0]
    artist = "未知艺术家"
    album = "未知专辑"
    duration = 0

    try:
        audio = MutagenFile(file_path, easy=True)
        if audio:
            title = audio.get("title", [title])[0] if audio.get("title") else title
            artist = audio.get("artist", [artist])[0] if audio.get("artist") else artist
            album = audio.get("album", [album])[0] if audio.get("album") else album
            info = getattr(audio, "info", None)
            if info:
                duration = int(getattr(info, "length", 0) or 0)
    except Exception:
        try:
            audio = MutagenFile(file_path)
            info = getattr(audio, "info", None)
            if info:
                duration = int(getattr(info, "length", 0) or 0)
        except Exception:
            pass

    return {
        "title": title,
        "artist": artist,
        "album": album,
        "duration": duration,
        "file_size": file_size,
        "format": ext,
    }


def extract_cover(file_path: str) -> str | None:
    try:
        audio = MutagenFile(file_path)
        if audio is None:
            return None

        pictures = []
        if hasattr(audio, "pictures"):
            pictures = audio.pictures
        elif hasattr(audio, "tags") and audio.tags:
            from mutagen.id3 import APIC

            pictures = [tag for tag in audio.tags.values() if isinstance(tag, APIC)]

        if not pictures:
            return None

        pic = pictures[0]
        cover_filename = f"{uuid.uuid4().hex}.jpg"
        cover_path = os.path.join(COVERS_DIR, cover_filename)
        with open(cover_path, "wb") as f:
            f.write(pic.data)
        return cover_path
    except Exception:
        return None


def delete_music_file(file_path: str):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


def delete_cover_file(cover_path: str | None):
    try:
        if cover_path and os.path.exists(cover_path):
            os.remove(cover_path)
    except Exception:
        pass
