from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .config import settings
import os
import ipaddress
from typing import Set, List
from collections import defaultdict
import time

# 从环境变量读取黑名单/白名单
def _parse_ip_list(ip_string: str) -> Set[str]:
    """解析 IP 列表，支持单个 IP 和 CIDR"""
    ips = set()
    if not ip_string:
        return ips
    
    for ip_str in ip_string.split(','):
        ip_str = ip_str.strip()
        if ip_str:
            try:
                # 验证 IP 格式
                ipaddress.ip_network(ip_str, strict=False)
                ips.add(ip_str)
            except ValueError:
                print(f"⚠️  无效的 IP 格式: {ip_str}")
    
    return ips

class IPFilterMiddleware(BaseHTTPMiddleware):
    """IP 过滤中间件 - 支持黑名单和白名单"""
    
    def __init__(self, app):
        super().__init__(app)
        self.blacklist = _parse_ip_list(os.getenv('IP_BLACKLIST', ''))
        self.whitelist = _parse_ip_list(os.getenv('IP_WHITELIST', ''))
        
        # 如果有白名单，则所有未在白名单中的 IP 都会被拒绝
        self.use_whitelist = bool(self.whitelist)
        
        # 访问统计（用于检测异常行为）
        self.ip_request_counts: defaultdict = defaultdict(int)
        self.ip_last_seen: dict = {}
        self.blacklisted_ips: Set[str] = set()
        
        # 阈值配置
        self.auto_blacklist_threshold = int(os.getenv('AUTO_BLACKLIST_THRESHOLD', '500'))  # 5分钟内超过500次请求
        self.auto_blacklist_window = int(os.getenv('AUTO_BLACKLIST_WINDOW', '300'))  # 300秒 = 5分钟
        self.ip_cleanup_interval = int(os.getenv('IP_CLEANUP_INTERVAL', '600'))  # 10分钟清理一次
        
        print(f"🔒 IP 过滤已配置: 黑名单={len(self.blacklist)}个, 白名单={len(self.whitelist)}个, 使用白名单={self.use_whitelist}")
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """检查 IP 是否被阻止"""
        # 检查动态黑名单
        if ip in self.blacklisted_ips:
            return True
        
        # 检查静态黑名单
        if self._ip_in_networks(ip, self.blacklist):
            return True
        
        return False
    
    def _ip_in_networks(self, ip: str, networks: Set[str]) -> bool:
        """检查 IP 是否在指定网络中"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for network in networks:
                network_obj = ipaddress.ip_network(network, strict=False)
                if ip_obj in network_obj:
                    return True
        except ValueError:
            pass
        return False
    
    def _is_ip_allowed(self, ip: str) -> bool:
        """检查 IP 是否被允许"""
        if self._is_ip_blocked(ip):
            return False
        
        # 如果使用白名单，检查 IP 是否在白名单中
        if self.use_whitelist:
            return self._ip_in_networks(ip, self.whitelist)
        
        return True
    
    def _track_ip(self, ip: str):
        """跟踪 IP 访问，检测异常行为"""
        now = time.time()
        
        # 增加计数
        self.ip_request_counts[ip] += 1
        self.ip_last_seen[ip] = now
        
        # 定期清理旧数据
        if now % self.ip_cleanup_interval < 1:
            cutoff = now - self.auto_blacklist_window
            for tracked_ip in list(self.ip_request_counts.keys()):
                if self.ip_last_seen.get(tracked_ip, 0) < cutoff:
                    del self.ip_request_counts[tracked_ip]
                    del self.ip_last_seen[tracked_ip]
        
        # 自动加入黑名单（可选功能）
        if self.ip_request_counts[ip] > self.auto_blacklist_threshold:
            print(f"⚠️  IP {ip} 在 {self.auto_blacklist_window} 秒内请求超过 {self.auto_blacklist_threshold} 次，自动加入黑名单")
            self.blacklisted_ips.add(ip)
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        path = request.url.path
        
        # 排除健康检查和文档
        if path in ['/health', '/ping', '/robots.txt']:
            return await call_next(request)
        
        # 获取客户端真实 IP
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
            request.headers.get("x-real-ip") or
            (request.client.host if request.client else "unknown")
        )
        
        # 检查 IP 是否被阻止
        if not self._is_ip_allowed(client_ip):
            print(f"🚫 拒绝访问: IP={client_ip}, Path={path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "message": "访问被拒绝",
                    "code": "IP_BLOCKED"
                }
            )
        
        # 跟踪 IP（用于异常检测）
        self._track_ip(client_ip)
        
        # 添加安全头
        response = await call_next(request)
        response.headers["X-Client-IP"] = client_ip
        
        return response


def setup_ip_filter(app):
    """设置 IP 过滤中间件"""
    ip_blacklist = os.getenv('IP_BLACKLIST', '')
    ip_whitelist = os.getenv('IP_WHITELIST', '')
    
    if ip_blacklist or ip_whitelist:
        print("🔒 启用 IP 过滤中间件")
        app.add_middleware(IPFilterMiddleware)
    else:
        print("ℹ️  IP 过滤未配置（黑名单和白名单都为空）")
