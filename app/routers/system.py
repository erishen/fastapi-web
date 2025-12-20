from fastapi import APIRouter

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