from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    color: str | None = "#000000"


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagOut(BaseModel):
    id: int
    name: str
    color: str | None = None

    model_config = {"from_attributes": True}
