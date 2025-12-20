from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas
from typing import List, Optional

def get_item(db: Session, item_id: int) -> Optional[models.Item]:
    """根据ID获取单个商品"""
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 10) -> List[models.Item]:
    """获取商品列表，支持分页"""
    return db.query(models.Item).order_by(desc(models.Item.created_at)).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    """创建新商品"""
    # 转换布尔值为整数（MySQL兼容）
    is_offer_int = 1 if item.is_offer else 0 if item.is_offer is not None else 0
    
    db_item = models.Item(
        name=item.name, 
        price=item.price, 
        is_offer=is_offer_int,
        description=item.description
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item(db: Session, item_id: int, item: schemas.ItemUpdate) -> Optional[models.Item]:
    """更新商品信息"""
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        # 只更新提供的字段
        update_data = item.model_dump(exclude_unset=True)
        
        # 处理布尔值转换
        if 'is_offer' in update_data:
            update_data['is_offer'] = 1 if update_data['is_offer'] else 0
        
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int) -> bool:
    """删除商品"""
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False

def search_items(db: Session, keyword: str, skip: int = 0, limit: int = 10) -> List[models.Item]:
    """搜索商品"""
    return db.query(models.Item).filter(
        models.Item.name.contains(keyword)
    ).order_by(desc(models.Item.created_at)).offset(skip).limit(limit).all()
