"""文档操作日志路由"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from sqlalchemy import desc
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import logging

from .. import models
from ..database import get_db
from ..redis_client import redis_client
from ..config import settings
from ..security import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/docs",
    tags=["文档日志"]
)

# 日志请求模型
class DocLogRequest(BaseModel):
    action: str
    doc_slug: str
    user_id: str
    user_email: str
    user_name: str
    auth_method: str
    details: Optional[str] = None

def verify_api_key(request: Request):
    """验证 API Key（生产环境必须配置）"""
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")

    # 生产环境必须配置 API Key
    if settings.app_env == "production" and not settings.doc_log_api_key:
        logger.error("DOC_LOG_API_KEY 未配置，拒绝访问")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器配置错误",
        )

    if settings.doc_log_api_key:
        if not api_key or api_key != settings.doc_log_api_key:
            # 记录失败尝试（脱敏）
            client_ip = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
                request.headers.get("x-real-ip") or
                (request.client.host if request.client else "unknown")
            )
            logger.warning(f"Invalid API key attempt from IP: {client_ip}")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的 API Key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
    return api_key

@router.post("/log")
async def log_doc_action(
    log_data: DocLogRequest = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    记录文档操作日志

    Args:
        log_data: 日志数据 (JSON body)
        request: 请求对象（用于速率限制）
        db: 数据库会话
        api_key: API Key（如果配置）
    """
    try:
        # 1. 记录到数据库
        log_entry = models.DocLog(
            action=log_data.action,
            doc_slug=log_data.doc_slug,
            user_id=log_data.user_id,
            user_email=log_data.user_email,
            user_name=log_data.user_name,
            auth_method=log_data.auth_method,
            details=log_data.details
        )
        db.add(log_entry)
        db.commit()

        # 2. 记录到 Redis（快速查询）
        log_key = f"doc:log:{datetime.now().strftime('%Y%m%d')}"
        await redis_client.lpush(log_key, {
            'action': log_data.action,
            'doc_slug': log_data.doc_slug,
            'user_email': log_data.user_email,
            'user_name': log_data.user_name,
            'auth_method': log_data.auth_method,
            'timestamp': datetime.now().isoformat(),
            'details': log_data.details
        })
        # 设置过期时间：7天
        await redis_client.expire(log_key, 7 * 24 * 60 * 60)

        # 审计日志（脱敏）
        if settings.debug:
            logger.info(f"Doc log created: action={log_data.action}, doc={log_data.doc_slug}, user={log_data.user_email}")

        return {"success": True, "message": "日志记录成功"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create doc log: {str(e)}")
        # 生产环境不暴露错误详情
        if settings.app_env == "production":
            raise HTTPException(
                status_code=500,
                detail="日志记录失败"
            )
        raise


@router.get("/logs")
async def get_doc_logs(
    request: Request,
    limit: int = 100,
    doc_slug: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    """
    获取文档操作日志（需要管理员权限）

    Args:
        request: 请求对象
        limit: 返回条数限制
        doc_slug: 按文档过滤
        action: 按操作类型过滤
        db: 数据库会话
        current_user: 当前用户（必须是管理员）
    """
    try:
        query = db.query(models.DocLog)

        # 应用过滤条件
        if doc_slug:
            query = query.filter(models.DocLog.doc_slug == doc_slug)
        if action:
            query = query.filter(models.DocLog.action == action)

        # 按时间倒序排序
        logs = query.order_by(desc(models.DocLog.timestamp)).limit(limit).all()

        # 审计日志（脱敏）
        if settings.debug:
            logger.info(f"Doc logs retrieved: count={len(logs)}, user={current_user.get('username')}")

        return {
            "success": True,
            "logs": [
                {
                    "id": log.id,
                    "action": log.action,
                    "doc_slug": log.doc_slug,
                    "user_id": log.user_id,
                    "user_email": log.user_email,
                    "user_name": log.user_name,
                    "auth_method": log.auth_method,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "details": log.details
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Failed to retrieve doc logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取日志失败" if settings.app_env == "production" else str(e)
        )


@router.get("/stats")
async def get_doc_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_admin_user)
):
    """
    获取文档操作统计（需要管理员权限）

    Args:
        request: 请求对象
        db: 数据库会话
        current_user: 当前用户（必须是管理员）
    Returns:
        各类操作的统计数据
    """
    try:
        # 获取最近7天的统计
        week_ago = datetime.now() - timedelta(days=7)
        recent_logs = db.query(models.DocLog).filter(
            models.DocLog.timestamp >= week_ago
        ).all()

        # 统计各类型操作
        stats = {
            "total": len(recent_logs),
            "create": len([l for l in recent_logs if l.action == "create"]),
            "update": len([l for l in recent_logs if l.action == "update"]),
            "delete": len([l for l in recent_logs if l.action == "delete"]),
            "by_user": {},
        }

        # 按用户统计
        for log in recent_logs:
            if log.user_email not in stats["by_user"]:
                stats["by_user"][log.user_email] = 0
            stats["by_user"][log.user_email] += 1

        return {"success": True, "stats": stats}

    except Exception as e:
        logger.error(f"Failed to retrieve doc stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取统计失败" if settings.app_env == "production" else str(e)
        )
