from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from .config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件"""

    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)

        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"

        # 防止 MIME 类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS 防护
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=(), "
            "autoplay=(self), encrypted-media=(self), fullscreen=(self)"
        )

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "frame-src 'none'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]

        # 根据环境设置不同的 CSP 策略
        if settings.debug:
            # 开发环境：放宽限制，支持 Swagger UI、ReDoc CDN 和热重载
            csp_directives.extend([
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: data: https://cdn.jsdelivr.net https://unpkg.com http://localhost:* http://127.0.0.1:*",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com http://localhost:* http://127.0.0.1:*",
                "img-src 'self' data: https: https://cdn.jsdelivr.net https://fonts.gstatic.com http://localhost:* http://127.0.0.1:*",
                "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com https://fonts.googleapis.com http://localhost:* http://127.0.0.1:*",
                "connect-src 'self' ws: wss: blob: data: https://cdn.jsdelivr.net https://unpkg.com http://localhost:* http://127.0.0.1:*",
                "worker-src 'self' blob: data: https://cdn.jsdelivr.net https://unpkg.com http://localhost:* http://127.0.0.1:*",
            ])
        else:
            # 生产环境：更严格的限制，但允许 API 文档 CDN
            csp_directives.extend([
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
                "img-src 'self' data: https: https://cdn.jsdelivr.net https://fonts.gstatic.com",
                "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com https://fonts.googleapis.com",
                "connect-src 'self' ws: wss:",
            ])

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # HSTS (仅生产环境)
        if settings.app_env == "production":
            hsts_value = "max-age=31536000; includeSubDomains; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # 移除可能泄露信息的头
        try:
            del response.headers["X-Powered-By"]
        except KeyError:
            pass
        try:
            del response.headers["Server"]
        except KeyError:
            pass

        return response


def setup_security_headers(app: FastAPI):
    """设置安全响应头中间件"""
    app.add_middleware(SecurityHeadersMiddleware)
