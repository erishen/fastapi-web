from sqlalchemy import create_engine
from app.models import Base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)

# 创建所有表
Base.metadata.create_all(bind=engine)
