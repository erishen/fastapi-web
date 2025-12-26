from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from .config import settings

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 HTTP 异常"""
    # 生产环境不暴露详细信息
    if settings.app_env == "production":
        # 记录错误但不返回详细信息
        logger.error(f"HTTP exception on {request.url.path}: {exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": "请求失败",
                "status_code": exc.status_code
            }
        )

    # 开发环境返回详细信息
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证异常"""
    # 生产环境不暴露详细验证错误
    if settings.app_env == "production":
        logger.error(f"Validation error on {request.url.path}")
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "message": "请求参数验证失败",
                "status_code": 422
            }
        )

    # 开发环境返回详细信息
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "请求参数验证失败",
            "details": exc.errors(),
            "status_code": 422,
            "path": str(request.url.path)
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    # 记录完整错误信息（包括堆栈跟踪）
    logger.error(
        f"Unhandled exception on {request.url.path}",
        exc_info=True,
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.headers.get("x-forwarded-for") or request.client.host if request.client else "unknown"
        }
    )

    # 生产环境不暴露错误信息
    if settings.app_env == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "服务器内部错误，请稍后重试",
                "status_code": 500
            }
        )

    # 开发环境返回详细信息
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": str(exc),
            "type": type(exc).__name__,
            "status_code": 500,
            "path": str(request.url.path)
        }
    )

def setup_exception_handlers(app):
    """设置异常处理器"""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)