from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .redis_client import redis_client
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json
import hashlib
from typing import Dict

def setup_cors(app: FastAPI):
    """配置 CORS 中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
        max_age=600,  # 10 分钟预检请求缓存
    )

# 速率限制配置
RATE_LIMITS: Dict[str, Dict[str, int]] = {
    "default": {
        "requests": 100,
        "window": 60  # 60 秒
    },
    "strict": {
        "requests": 20,
        "window": 60
    },
    "login": {
        "requests": 5,
        "window": 900  # 15 分钟
    }
}

class RateLimitMiddleware(BaseHTTPMiddleware):
    """改进的速率限制中间件"""

    def __init__(self, app):
        super().__init__(app)

    def _get_rate_limit_config(self, path: str, method: str) -> Dict[str, int]:
        """根据路径和请求方法获取速率限制配置"""
        # 登录相关请求使用严格限制
        if "/auth/login" in path:
            return RATE_LIMITS["login"]

        # 文档日志 POST 使用严格限制
        if path == "/api/docs/log" and method == "POST":
            return RATE_LIMITS["strict"]

        # 其他请求使用默认限制
        return RATE_LIMITS["default"]

    async def dispatch(self, request: Request, call_next):
        # 对所有需要保护的路径进行速率限制
        path = request.url.path

        # 排除健康检查等公开接口
        if path in ["/health", "/ping", "/api/docs", "/redoc"]:
            return await call_next(request)

        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
            request.headers.get("x-real-ip") or
            (request.client.host if request.client else "unknown")
        )

        # 获取速率限制配置
        rate_config = self._get_rate_limit_config(path, request.method)
        rate_key = f"ratelimit:{path}:{client_ip}"

        try:
            # 获取当前计数
            current = await redis_client.get(rate_key)
            current = int(current) if current else 0

            # 检查是否超过限制
            if current >= rate_config["requests"]:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": True,
                        "message": "请求过于频繁，请稍后再试",
                        "limit": rate_config["requests"],
                        "window": rate_config["window"]
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_config["requests"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(rate_config["window"]),
                        "Retry-After": str(rate_config["window"])
                    }
                )

            # 增加计数
            await redis_client.set(rate_key, str(current + 1), rate_config["window"])

            response = await call_next(request)

            # 添加速率限制响应头
            remaining = max(0, rate_config["requests"] - current - 1)
            response.headers["X-RateLimit-Limit"] = str(rate_config["requests"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)

            return response

        except Exception as e:
            if settings.debug:
                print(f"Rate limit error: {e}")
            # Redis 出错时不限制，继续请求（fail-open 策略）
            return await call_next(request)

def setup_middleware(app: FastAPI):
    """设置所有中间件"""
    setup_cors(app)
    # 添加速率限制中间件
    app.add_middleware(RateLimitMiddleware)