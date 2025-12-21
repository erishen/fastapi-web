import redis.asyncio as redis
from typing import Optional, Any
import json
import pickle
from .config import settings

class RedisClient:
    """Redis 客户端封装"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """连接 Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            await self.redis_client.ping()
            print("✅ Redis 连接成功")
        except Exception as e:
            print(f"❌ Redis 连接失败: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """断开 Redis 连接"""
        if self.redis_client:
            await self.redis_client.close()
            print("🔌 Redis 连接已关闭")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取值"""
        if not self.redis_client:
            return None
        try:
            value = await self.redis_client.get(key)
            if value:
                # 尝试解析 JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            print(f"Redis GET 错误: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置值"""
        if not self.redis_client:
            return False
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)
            
            result = await self.redis_client.set(key, value, ex=expire)
            return bool(result)
        except Exception as e:
            print(f"Redis SET 错误: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除键"""
        if not self.redis_client:
            return False
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            print(f"Redis DELETE 错误: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis_client:
            return False
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            print(f"Redis EXISTS 错误: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self.redis_client:
            return False
        try:
            result = await self.redis_client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            print(f"Redis EXPIRE 错误: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        if not self.redis_client:
            return -1
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            print(f"Redis TTL 错误: {e}")
            return -1
    
    async def keys(self, pattern: str = "*") -> list:
        """获取匹配的键列表"""
        if not self.redis_client:
            return []
        try:
            return await self.redis_client.keys(pattern)
        except Exception as e:
            print(f"Redis KEYS 错误: {e}")
            return []
    
    async def flushdb(self) -> bool:
        """清空当前数据库"""
        if not self.redis_client:
            return False
        try:
            result = await self.redis_client.flushdb()
            return bool(result)
        except Exception as e:
            print(f"Redis FLUSHDB 错误: {e}")
            return False

# 全局 Redis 客户端实例
redis_client = RedisClient()

# 缓存装饰器
def cache_result(key_prefix: str, expire: int = 3600):
    """缓存结果装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached_result = await redis_client.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await redis_client.set(cache_key, result, expire)
            return result
        return wrapper
    return decorator