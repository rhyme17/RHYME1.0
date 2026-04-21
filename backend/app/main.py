from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import auth, musics, online, tags
from app.config import CORS_ORIGINS
from app.database import Base, engine
from app.utils.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from app.utils.logging_utils import setup_logging

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("RHYME Music Server 启动")
    yield
    logger.info("RHYME Music Server 关闭")


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(title="RHYME Music Server", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(musics.router, prefix="/api/musics", tags=["音乐"])
app.include_router(online.router, prefix="/api/online", tags=["在线音乐"])
app.include_router(tags.router, prefix="/api/tags", tags=["标签"])


@app.get("/")
def root():
    return {"name": "RHYME Music Server", "version": "1.0.0"}
