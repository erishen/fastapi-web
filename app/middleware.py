from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .redis_client import redis_client
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json
import hashlib

def setup_cors(app: FastAPI):
    """配置 CORS 中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # 只对 /api/docs/log 路径进行速率限制
        if request.url.path == "/api/docs/log" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            rate_key = f"ratelimit:doclog:{client_ip}"
            
            # 检查当前请求次数
            try:
                current = await redis_client.get(rate_key)
                current = int(current) if current else 0
                
                if current >= settings.doc_log_rate_limit:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"error": True, "message": f"请求过于频繁，请稍后再试"}
                    )
                
                # 增加计数
                await redis_client.set(rate_key, str(current + 1), settings.doc_log_rate_limit_window)
            except Exception as e:
                # Redis 出错时不限制，继续请求
                print(f"Rate limit error: {e}")
        
        response = await call_next(request)
        return response

def setup_middleware(app: FastAPI):
    """设置所有中间件"""
    setup_cors(app)
    # 添加速率限制中间件
    app.add_middleware(RateLimitMiddleware)