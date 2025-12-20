from pydantic import BaseModel, Field
from typing import Union, Optional
from datetime import datetime

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="商品名称")
    price: float = Field(..., gt=0, description="商品价格，必须大于0")
    is_offer: Union[bool, None] = Field(default=None, description="是否为特价商品")
    description: Optional[str] = Field(None, max_length=1000, description="商品描述")

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    is_offer: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=1000)

class Item(ItemBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2 语法
