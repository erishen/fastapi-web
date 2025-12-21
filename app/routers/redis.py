from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
from ..redis_client import redis_client
from ..security import get_current_user, get_admin_user
from pydantic import BaseModel
import json

router = APIRouter(
    prefix="/redis",
    tags=["Redis 缓存"],
    responses={404: {"description": "键未找到"}}
)

class RedisSetRequest(BaseModel):
    key: str
    value: Any
    expire: int = None

class RedisResponse(BaseModel):
    success: bool
    message: str
    data: Any = None

@router.get("/ping")
async def ping_redis():
    """测试 Redis 连接"""
    if not redis_client.redis_client:
        raise HTTPException(status_code=503, detail="Redis 未连接")
    
    try:
        await redis_client.redis_client.ping()
        return {"status": "ok", "message": "Redis 连接正常"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis 连接失败: {str(e)}")

@router.get("/keys", response_model=List[str])
async def get_keys(
    pattern: str = Query("*", description="键匹配模式"),
    current_user: dict = Depends(get_current_user)
):
    """获取所有匹配的键"""
    keys = await redis_client.keys(pattern)
    return keys

@router.get("/get/{key}")
async def get_value(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """获取指定键的值"""
    value = await redis_client.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="键不存在")
    
    return {
        "key": key,
        "value": value,
        "ttl": await redis_client.ttl(key)
    }

@router.post("/set", response_model=RedisResponse)
async def set_value(
    request: RedisSetRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """设置键值对"""
    success = await redis_client.set(request.key, request.value, request.expire)
    
    if success:
        return RedisResponse(
            success=True,
            message="设置成功",
            data={"key": request.key, "value": request.value}
        )
    else:
        raise HTTPException(status_code=500, detail="设置失败")

@router.delete("/delete/{key}", response_model=RedisResponse)
async def delete_key(
    key: str,
    admin_user: dict = Depends(get_admin_user)
):
    """删除指定键"""
    success = await redis_client.delete(key)
    
    if success:
        return RedisResponse(
            success=True,
            message="删除成功",
            data={"key": key}
        )
    else:
        raise HTTPException(status_code=404, detail="键不存在")

@router.post("/expire/{key}", response_model=RedisResponse)
async def set_expire(
    key: str,
    seconds: int = Query(..., gt=0, description="过期时间（秒）"),
    admin_user: dict = Depends(get_admin_user)
):
    """设置键的过期时间"""
    exists = await redis_client.exists(key)
    if not exists:
        raise HTTPException(status_code=404, detail="键不存在")
    
    success = await redis_client.expire(key, seconds)
    
    if success:
        return RedisResponse(
            success=True,
            message="设置过期时间成功",
            data={"key": key, "expire_seconds": seconds}
        )
    else:
        raise HTTPException(status_code=500, detail="设置过期时间失败")

@router.get("/ttl/{key}")
async def get_ttl(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """获取键的剩余过期时间"""
    ttl = await redis_client.ttl(key)
    
    if ttl == -2:
        raise HTTPException(status_code=404, detail="键不存在")
    
    return {
        "key": key,
        "ttl": ttl,
        "status": "永不过期" if ttl == -1 else f"{ttl}秒后过期"
    }

@router.post("/flushdb", response_model=RedisResponse)
async def flush_database(
    admin_user: dict = Depends(get_admin_user)
):
    """清空当前数据库（危险操作）"""
    success = await redis_client.flushdb()
    
    if success:
        return RedisResponse(
            success=True,
            message="数据库已清空",
            data=None
        )
    else:
        raise HTTPException(status_code=500, detail="清空数据库失败")

@router.get("/stats")
async def get_redis_stats(
    current_user: dict = Depends(get_current_user)
):
    """获取 Redis 统计信息"""
    if not redis_client.redis_client:
        raise HTTPException(status_code=503, detail="Redis 未连接")
    
    try:
        info = await redis_client.redis_client.info()
        keys_count = len(await redis_client.keys("*"))
        
        return {
            "connected": True,
            "keys_count": keys_count,
            "memory_used": info.get("used_memory_human", "N/A"),
            "uptime": info.get("uptime_in_seconds", 0),
            "version": info.get("redis_version", "N/A"),
            "connected_clients": info.get("connected_clients", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"获取统计信息失败: {str(e)}")

# 缓存示例接口
@router.get("/cache/example")
async def cache_example(
    name: str = Query("World", description="名称"),
    current_user: dict = Depends(get_current_user)
):
    """缓存示例 - 演示如何使用 Redis 缓存"""
    cache_key = f"greeting:{name}"
    
    # 尝试从缓存获取
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        return {
            "message": cached_result,
            "from_cache": True,
            "ttl": await redis_client.ttl(cache_key)
        }
    
    # 生成新结果并缓存
    result = f"Hello, {name}! Current time: {__import__('datetime').datetime.now()}"
    await redis_client.set(cache_key, result, 60)  # 缓存 60 秒
    
    return {
        "message": result,
        "from_cache": False,
        "cached_for": 60
    }