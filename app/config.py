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
    debug: bool = os.getenv('DEBUG', 'true').lower() == 'true'  # 默认 True，生产环境设为 false
    
    # 数据库配置
    database_url: str = "sqlite:///./app.db"
    
    # Redis 配置
    redis_url: str = os.getenv('REDIS_URL', 'redis://:redispassword@localhost:6380/0')
    redis_host: str = os.getenv('REDIS_HOST', 'localhost')
    redis_port: int = int(os.getenv('REDIS_PORT', '6380'))
    redis_db: int = int(os.getenv('REDIS_DB', '0'))
    redis_password: str = os.getenv('REDIS_PASSWORD', 'redispassword')
    
    # API 文档配置
    docs_url: str = "/docs"
    redoc_url: Optional[str] = None  # 使用自定义 ReDoc
    openapi_url: str = "/openapi.json"
    
    # CORS 配置（开发环境宽松，生产环境严格）
    app_env: str = os.getenv('APP_ENV', 'development')
    allowed_origins: List[str] = ["*"] if app_env == "development" else [
        x for x in [
            "http://localhost:3000",
            "http://localhost:3003",
            os.getenv('WEB_URL', ''),
            os.getenv('ADMIN_URL', ''),
        ] if x  # 移除空字符串
    ]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["Content-Type", "Authorization", "X-User-Id", "X-User-Email", "X-API-Key"]
    allow_credentials: bool = True
    
    # 日志配置
    log_level: str = "info"
    
    # 环境变量
    app_env: str = "development"
    
    # JWT 配置（来自 .env 文件）
    secret_key: str = os.getenv('SECRET_KEY', os.urandom(32).hex())
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

    # NextAuth 配置（用于验证 NextAuth token）
    nextauth_secret: str = os.getenv('NEXTAUTH_SECRET', '')

    # 允许的 admin 用户邮箱（来自 NextAuth）
    nextauth_admin_emails: str = os.getenv('NEXTAUTH_ADMIN_EMAILS', '')  # 逗号分隔的邮箱列表

    # 管理员凭据（来自 .env 文件）
    admin_username: str = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password_hash: str = os.getenv('ADMIN_PASSWORD_HASH', '')  # 预计算的密码哈希
    admin_password: str = os.getenv('ADMIN_PASSWORD', 'secret')  # 兼容：如果未提供哈希则使用明文并警告
    
    # 缓存配置
    cache_expire_seconds: int = 3600  # 1小时
    
    # 日志 API 保护配置
    doc_log_api_key: str = os.getenv('DOC_LOG_API_KEY', '')
    doc_log_rate_limit: int = int(os.getenv('DOC_LOG_RATE_LIMIT', '100'))  # 每分钟最多100次请求
    doc_log_rate_limit_window: int = int(os.getenv('DOC_LOG_RATE_LIMIT_WINDOW', '60'))  # 时间窗口（秒）
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 忽略额外字段
        extra = "ignore"

# 全局配置实例
settings = Settings()