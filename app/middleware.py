from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

def setup_cors(app: FastAPI):
    """配置 CORS 中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

def setup_middleware(app: FastAPI):
    """设置所有中间件"""
    setup_cors(app)