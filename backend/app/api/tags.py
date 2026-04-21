from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_admin_user, get_current_user
from app.database import get_db
from app.models.music import Music
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagOut, TagUpdate

router = APIRouter()


@router.get("/", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db)):
    return db.query(Tag).order_by(Tag.name).all()


@router.post("/", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(data: TagCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    existing = db.query(Tag).filter(Tag.name == data.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签已存在")
    tag = Tag(name=data.name, color=data.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagOut)
def update_tag(
    tag_id: int,
    data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != tag.name:
        existing = db.query(Tag).filter(Tag.name == update_data["name"]).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签名已存在")

    for key, value in update_data.items():
        setattr(tag, key, value)

    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")
    db.delete(tag)
    db.commit()


@router.post("/{music_id}/tags/{tag_id}", response_model=dict)
def add_tag_to_music(
    music_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    music = db.query(Music).filter(Music.id == music_id).first()
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音乐不存在")

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")

    if tag in music.tags:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签已关联")

    music.tags.append(tag)
    db.commit()
    return {"detail": "标签已添加"}


@router.delete("/{music_id}/tags/{tag_id}", response_model=dict)
def remove_tag_from_music(
    music_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    music = db.query(Music).filter(Music.id == music_id).first()
    if not music:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音乐不存在")

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")

    if tag not in music.tags:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标签未关联")

    music.tags.remove(tag)
    db.commit()
    return {"detail": "标签已移除"}
