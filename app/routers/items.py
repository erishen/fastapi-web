from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..database import get_db
from ..auth import get_current_user, get_admin_user

router = APIRouter(
    prefix="/items",
    tags=["商品管理"],
    responses={404: {"description": "商品未找到"}}
)

@router.get("/", response_model=List[schemas.Item])
def read_items(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 需要认证
):
    """获取商品列表"""
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@router.get("/search", response_model=List[schemas.Item])
def search_items(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 需要认证
):
    """搜索商品"""
    items = crud.search_items(db, keyword=keyword, skip=skip, limit=limit)
    return items

@router.get("/{item_id}", response_model=schemas.Item)
def read_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 需要认证
):
    """获取单个商品"""
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="商品未找到")
    return db_item

@router.post("/", response_model=schemas.Item, status_code=201)
def create_item(
    item: schemas.ItemCreate, 
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)  # 需要管理员权限
):
    """创建新商品"""
    return crud.create_item(db=db, item=item)

@router.put("/{item_id}", response_model=schemas.Item)
def update_item(
    item_id: int, 
    item: schemas.ItemUpdate, 
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)  # 需要管理员权限
):
    """更新商品信息"""
    db_item = crud.update_item(db=db, item_id=item_id, item=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="商品未找到")
    return db_item

@router.delete("/{item_id}")
def delete_item(
    item_id: int, 
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)  # 需要管理员权限
):
    """删除商品"""
    success = crud.delete_item(db=db, item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="商品未找到")
    return {"message": "商品删除成功"}