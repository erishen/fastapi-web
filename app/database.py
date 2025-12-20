from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

# MySQL 连接配置
engine = create_engine(
    DATABASE_URL,
    # MySQL 特定配置
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_recycle=3600,   # 1小时后回收连接
    echo=False,          # 设置为 True 可以看到 SQL 语句
    connect_args={
        "charset": "utf8mb4",
        "autocommit": False
    } if "mysql" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False
