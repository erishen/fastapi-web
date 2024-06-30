from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    price = Column(Float, nullable=False)
    is_offer = Column(Integer, nullable=True)  # SQLite does not support Boolean type well, using Integer
