from datetime import datetime

from pydantic import BaseModel, computed_field


class MusicCreate(BaseModel):
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    tag_ids: list[int] | None = None


class MusicUpdate(BaseModel):
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    tag_ids: list[int] | None = None


class TagBrief(BaseModel):
    id: int
    name: str
    color: str | None = None

    model_config = {"from_attributes": True}


class MusicOut(BaseModel):
    id: int
    title: str
    artist: str
    album: str
    duration: int
    file_size: int
    format: str
    has_cover: bool = False
    created_at: datetime
    uploader_id: int | None = None
    tags: list[TagBrief] = []

    @computed_field
    @property
    def stream_url(self) -> str:
        return f"/api/musics/{self.id}/stream"

    @computed_field
    @property
    def download_url(self) -> str:
        return f"/api/musics/{self.id}/download"

    @computed_field
    @property
    def cover_url(self) -> str | None:
        return f"/api/musics/{self.id}/cover" if self.has_cover else None

    model_config = {"from_attributes": True}


class MusicListOut(BaseModel):
    total: int
    items: list[MusicOut]
