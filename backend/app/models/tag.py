from sqlalchemy import Column, ForeignKey, Integer, String, Table

from app.database import Base

music_tags = Table(
    "music_tags",
    Base.metadata,
    Column("music_id", Integer, ForeignKey("musics.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), nullable=True, default="#000000")
