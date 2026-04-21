from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging_utils import setup_logging

logger = setup_logging()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.exception("未处理的异常: %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"detail": "服务器内部错误"},
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info("%s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("%s %s -> %d", request.method, request.url.path, response.status_code)
        return response
