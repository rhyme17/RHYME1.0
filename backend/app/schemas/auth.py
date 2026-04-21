from pydantic import BaseModel, field_validator


class UserRegister(BaseModel):
    username: str
    password: str
    email: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码长度不能少于6位")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 50:
            raise ValueError("用户名长度需在2-50之间")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    github_login: str | None = None
    github_avatar: str | None = None
    is_admin: bool
    is_active: bool

    model_config = {"from_attributes": True}
