from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基本信息
    app_name: str = "FastAPI Web Application"
    app_description: str = "一个基于 FastAPI 的商品管理系统"
    app_version: str = "1.0.0"
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = True
    
    # 数据库配置
    database_url: str = "sqlite:///./app.db"
    
    # API 文档配置
    docs_url: str = "/docs"
    redoc_url: Optional[str] = None  # 使用自定义 ReDoc
    openapi_url: str = "/openapi.json"
    
    # CORS 配置
    allowed_origins: List[str] = ["*"]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]
    allow_credentials: bool = True
    
    # 日志配置
    log_level: str = "info"
    
    # 环境变量
    app_env: str = "development"
    
    # 其他配置（来自 .env 文件）
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 忽略额外字段
        extra = "ignore"

# 全局配置实例
settings = Settings()