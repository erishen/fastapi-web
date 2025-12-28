from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Set, List, Pattern
import re
import os

# 敏感路径列表（会被直接拦截）
SENSITIVE_PATTERNS: List[str] = [
    r'\.env',
    r'\.env\.',
    r'\.git',
    r'\.hg',
    r'\.svn',
    r'\.idea',
    r'\.vscode',
    r'\.dockerignore',
    r'\.gitignore',
    r'\.DS_Store',
    r'\.DS_Store?',
    r'thumbs\.db',
    r'\.bak$',
    r'\.backup$',
    r'\.old$',
    r'\.tmp$',
    r'\.swp$',
    r'\.swo$',
    r'\.log$',
    r'\.sql$',
    r'\.key$',
    r'\.pem$',
    r'\.crt$',
    r'\.p12$',
    r'\.keystore$',
    r'\.jks$',
    r'\.wallet$',
    r'\.db$',
    r'\.sqlite',
    r'\.mdb$',
    r'\.config$',
    r'\.secret$',
    r'\.password',
    r'\.auth',
    r'\.token',
    r'\.credentials$',
    r'\.credentials',
    r'sendgrid\.env',
    r'\.prod$',
    r'\.dev$',
    r'\.local$',
    r'\.staging$',
]

# 爬虫可疑路径（记录但允许）
CRAWLER_SUSPICIOUS_PATTERNS: List[str] = [
    r'/admin',
    r'/login',
    r'/wp-',
    r'/wordpress',
    r'/phpmyadmin',
    r'/mysql',
    r'/backup',
    r'/setup',
    r'/install',
    r'/test',
    r'/debug',
    r'/dns-query',
    r'/actuator',
    r'/api-docs',
    r'/v1/models',  # OpenAI/AI API 扫描
    r'/v1/completions',  # AI 模型调用
    r'/v1/chat',  # AI 聊天 API
    r'/api/v1',  # API 版本探测
    r'/graphql',  # GraphQL 探测
    r'/favicon.ico',  # 图标请求（爬虫）
]

class PathProtectionMiddleware(BaseHTTPMiddleware):
    """敏感路径保护中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        # 编译正则表达式
        self.sensitive_regex = [re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS]
        self.crawler_regex = [re.compile(pattern, re.IGNORECASE) for pattern in CRAWLER_SUSPICIOUS_PATTERNS]
        
        # 启用严格模式（从环境变量读取）
        self.strict_mode = os.getenv('PATH_PROTECTION_STRICT', 'false').lower() == 'true'
        
        print(f"🛡️  路径保护已启用: 敏感模式={len(self.sensitive_regex)}个, 可疑模式={len(self.crawler_regex)}个, 严格模式={self.strict_mode}")
    
    def _is_sensitive_path(self, path: str) -> bool:
        """检查是否为敏感路径"""
        return any(pattern.search(path) for pattern in self.sensitive_regex)
    
    def _is_suspicious_path(self, path: str) -> bool:
        """检查是否为可疑路径（爬虫探测）"""
        return any(pattern.search(path) for pattern in self.crawler_regex)
    
    def _log_suspicious_access(self, path: str, client_ip: str, user_agent: str):
        """记录可疑访问"""
        print(f"⚠️  可疑访问检测: IP={client_ip}, Path={path}, UA={user_agent[:100]}")
        
        # 可以在这里添加更多告警逻辑，比如发送到日志系统、Slack等
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        path = request.url.path
        
        # 检查是否为敏感路径（直接拦截）
        if self._is_sensitive_path(path):
            client_ip = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
                request.headers.get("x-real-ip") or
                (request.client.host if request.client else "unknown")
            )
            user_agent = request.headers.get("user-agent", "unknown")
            
            print(f"🚫 阻止敏感路径访问: IP={client_ip}, Path={path}, UA={user_agent[:100]}")
            
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "message": "Not Found",
                    "code": "PATH_BLOCKED"
                }
            )
        
        # 检查是否为可疑路径（记录但允许）
        if self._is_suspicious_path(path):
            client_ip = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
                request.headers.get("x-real-ip") or
                (request.client.host if request.client else "unknown")
            )
            user_agent = request.headers.get("user-agent", "unknown")
            
            self._log_suspicious_access(path, client_ip, user_agent)
            
            # 严格模式下，可疑路径也会被阻止
            if self.strict_mode:
                print(f"🚫 严格模式阻止可疑路径: IP={client_ip}, Path={path}")
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": True,
                        "message": "Not Found",
                        "code": "SUSPICIOUS_PATH"
                    }
                )
        
        # 添加安全头
        response = await call_next(request)
        
        # 移除可能泄露服务器信息的头
        try:
            del response.headers["X-Powered-By"]
        except KeyError:
            pass
        
        return response


def setup_path_protection(app):
    """设置路径保护中间件"""
    print("🛡️  启用路径保护中间件")
    app.add_middleware(PathProtectionMiddleware)
