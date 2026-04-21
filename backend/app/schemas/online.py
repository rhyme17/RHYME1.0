from pydantic import BaseModel


class OnlineSearchResult(BaseModel):
    id: str
    name: str
    artist: list[list[str]]
    album: str
    source: str
    url_id: str = ""
    pic_id: str = ""
    lyric_id: str = ""


class OnlineSearchResponse(BaseModel):
    total: int
    items: list[OnlineSearchResult]


class OnlineUrlResponse(BaseModel):
    url: str


class OnlineLyricResponse(BaseModel):
    lyric: str


class OnlinePicResponse(BaseModel):
    url: str


class UnifiedLibraryItem(BaseModel):
    source: str = "library"
    id: str
    name: str
    artist: str
    album: str
    duration: int = 0
    format: str = ""
    has_cover: bool = False
    stream_url: str = ""
    cover_url: str | None = None


class UnifiedOnlineItem(BaseModel):
    source: str = "online"
    id: str
    name: str
    artist: str
    album: str = ""
    url_id: str = ""
    pic_id: str = ""
    lyric_id: str = ""


class UnifiedSearchResponse(BaseModel):
    library: list[UnifiedLibraryItem]
    online: list[UnifiedOnlineItem]


class ImportResponse(BaseModel):
    imported: bool
    music: dict | None = None
