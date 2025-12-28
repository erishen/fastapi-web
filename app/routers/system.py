from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(
    tags=["系统管理"]
)

@router.get("/")
def read_root():
    """根路径"""
    return {
        "message": "欢迎使用 FastAPI Web 应用",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }

@router.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "database": "connected"}

@router.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
def robots():
    """robots.txt - 限制爬虫访问敏感路径"""
    return """User-agent: *
Disallow: /api/
Disallow: /admin/
Disallow: /docs/
Disallow: /redoc/
Disallow: /openapi.json
Disallow: /auth/
Disallow: /redis/

# 允许搜索引擎访问公开页面
Allow: /
"""