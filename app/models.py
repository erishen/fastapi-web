from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    price = Column(Float, nullable=False)
    is_offer = Column(Integer, default=0)  # 0=False, 1=True
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DocLog(Base):
    """文档操作日志模型"""
    __tablename__ = "doc_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False, index=True)  # 操作类型: create/update/delete
    doc_slug = Column(String(100), nullable=False, index=True)  # 文档标识
    user_id = Column(String(100), nullable=True, index=True)  # 用户ID
    user_email = Column(String(100), nullable=True, index=True)  # 用户邮箱
    user_name = Column(String(100), nullable=True)  # 用户名
    auth_method = Column(String(50), nullable=True)  # 认证方式: nextauth/passport
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # 操作时间
    details = Column(Text, nullable=True)  # 操作详情（可选）
