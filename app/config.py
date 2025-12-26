from pydantic_settings import BaseSettings
from pydantic import ValidationError
from typing import List, Optional
import os
import secrets

class Settings(BaseSettings):
    """应用配置"""

    # 应用基本信息
    app_name: str = "FastAPI Web Application"
    app_description: str = "一个基于 FastAPI 的商品管理系统"
    app_version: str = "1.0.0"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'  # 默认 False，开发环境可设为 true

    # 数据库配置
    database_url: str = "sqlite:///./app.db"

    # Redis 配置
    redis_url: str = os.getenv('REDIS_URL', 'redis://:change-redis-password-in-production@localhost:6380/0')
    redis_host: str = os.getenv('REDIS_HOST', 'localhost')
    redis_port: int = int(os.getenv('REDIS_PORT', '6380'))
    redis_db: int = int(os.getenv('REDIS_DB', '0'))
    redis_password: str = os.getenv('REDIS_PASSWORD', 'change-redis-password-in-production')

    # API 文档配置
    docs_url: str = "/docs"
    redoc_url: Optional[str] = None  # 使用自定义 ReDoc
    openapi_url: str = "/openapi.json"

    # CORS 配置（严格限制）
    app_env: str = os.getenv('APP_ENV', 'development')
    allowed_origins: List[str] = [
        x for x in [
            "http://localhost:3000",
            "http://localhost:3003",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3003",
            "http://127.0.0.1:8080",
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

    # JWT 配置（强制使用强密钥）
    @property
    def secret_key(self) -> str:
        """获取 JWT 密钥，生产环境必须设置强密钥"""
        secret = os.getenv('SECRET_KEY')
        if not secret:
            if self.app_env == 'production':
                raise ValueError(
                    'SECRET_KEY 环境变量未设置。'
                    '生产环境必须设置强密钥。'
                    '请使用: openssl rand -hex 32 生成'
                )
            # 开发环境使用随机密钥
            return secrets.token_hex(32)
        # 验证密钥长度（至少 32 字节）
        if len(secret) < 32:
            raise ValueError(
                'SECRET_KEY 长度必须至少 32 字符。'
                '请使用: openssl rand -hex 32 生成更强的密钥'
            )
        return secret

    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

    # NextAuth 配置（用于验证 NextAuth token）
    nextauth_secret: str = os.getenv('NEXTAUTH_SECRET', '')

    # 允许的 admin 用户邮箱（来自 NextAuth）
    nextauth_admin_emails: str = os.getenv('NEXTAUTH_ADMIN_EMAILS', '')  # 逗号分隔的邮箱列表

    # 管理员凭据（只允许哈希密码）
    admin_username: str = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password_hash: str = os.getenv('ADMIN_PASSWORD_HASH', '')  # 预计算的密码哈希

    @property
    def admin_password_hash_required(self) -> str:
        """强制使用密码哈希"""
        if not self.admin_password_hash:
            if self.app_env == 'production':
                raise ValueError(
                    'ADMIN_PASSWORD_HASH 环境变量未设置。'
                    '生产环境必须使用哈希密码。'
                    '请使用: python generate_password_hash.py <password> 生成哈希'
                )
            # 开发环境警告并生成临时哈希
            print('⚠️  警告: 未设置 ADMIN_PASSWORD_HASH，使用临时哈希（仅开发环境）')
            return '$pbkdf2-sha256$30000$default$insecure'
        return self.admin_password_hash

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
try:
    settings = Settings()
except ValidationError as e:
    print(f"❌ 配置错误: {e}")
    print("\n请检查 .env 文件中的配置项")
    raise
except ValueError as e:
    print(f"❌ 安全配置错误: {e}")
    raise