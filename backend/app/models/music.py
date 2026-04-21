from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.tag import music_tags


class Music(Base):
    __tablename__ = "musics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, default="未知歌曲")
    artist = Column(String(100), nullable=False, default="未知艺术家")
    album = Column(String(100), nullable=False, default="未知专辑")
    file_path = Column(String(500), nullable=False)
    cover_path = Column(String(500), nullable=True)
    duration = Column(Integer, nullable=False, default=0)
    file_size = Column(Integer, nullable=False, default=0)
    format = Column(String(10), nullable=False, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    tags = relationship("Tag", secondary=music_tags, backref="musics", lazy="selectin")
