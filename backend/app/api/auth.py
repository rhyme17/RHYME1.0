from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import (
    ADMIN_GITHUB_IDS,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_REDIRECT_URI,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserOut, UserRegister
from app.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


@router.post("/register", response_model=UserOut)
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        email=data.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


@router.get("/github/authorize")
def github_authorize():
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="未配置 GitHub OAuth")
    params = f"client_id={GITHUB_CLIENT_ID}&redirect_uri={GITHUB_REDIRECT_URI}&scope=read:user,user:email&response_type=code"
    return {"url": f"https://github.com/login/oauth/authorize?{params}"}


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    import httpx

    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="未配置 GitHub OAuth")

    token_resp = httpx.post(
        "https://github.com/login/oauth/access_token",
        json={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI,
        },
        headers={"Accept": "application/json"},
    )
    token_data = token_resp.json()
    access_token_github = token_data.get("access_token")
    if not access_token_github:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub 授权失败")

    user_resp = httpx.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token_github}"},
    )
    github_user = user_resp.json()
    github_id = github_user.get("id")
    github_login = github_user.get("login")
    github_avatar = github_user.get("avatar_url")
    github_email = github_user.get("email")

    if not github_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="获取 GitHub 用户信息失败")

    user = db.query(User).filter(User.github_id == github_id).first()
    if not user:
        username = github_login or f"github_{github_id}"
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            username = f"{username}_{github_id}"

        is_admin = github_id in ADMIN_GITHUB_IDS

        user = User(
            username=username,
            github_id=github_id,
            github_login=github_login,
            github_avatar=github_avatar,
            email=github_email,
            is_admin=is_admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.github_login = github_login
        user.github_avatar = github_avatar
        if github_id in ADMIN_GITHUB_IDS:
            user.is_admin = True
        if not user.email and github_email:
            user.email = github_email
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(data={"sub": str(user.id)})

    frontend_url = GITHUB_REDIRECT_URI.rsplit("/api/", 1)[0]
    redirect_url = f"{frontend_url}/auth/callback?token={jwt_token}&is_admin={'1' if user.is_admin else '0'}"

    return RedirectResponse(url=redirect_url)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
