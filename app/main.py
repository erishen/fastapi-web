from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from . import crud, models, schemas
from .database import SessionLocal, engine, get_db
from dotenv import load_dotenv
import os

load_dotenv()

# 创建数据表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Web Application",
    description="一个基于 FastAPI 的商品管理系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,  # 禁用默认的 redoc
    openapi_url="/openapi.json"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义 ReDoc 页面
@app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def custom_redoc():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FastAPI Web Application - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: 'Roboto', sans-serif;
            }
            .loading {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                font-size: 18px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="loading" id="loading">正在加载 API 文档...</div>
        <div id="redoc-container"></div>
        
        <script src="https://unpkg.com/redoc@2.0.0/bundles/redoc.standalone.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const loading = document.getElementById('loading');
                const container = document.getElementById('redoc-container');
                
                try {
                    Redoc.init('/openapi.json', {
                        theme: {
                            colors: {
                                primary: {
                                    main: '#32329f'
                                }
                            }
                        }
                    }, container);
                    
                    // 隐藏加载提示
                    loading.style.display = 'none';
                } catch (error) {
                    loading.innerHTML = '加载失败，请尝试刷新页面或使用 <a href="/docs">Swagger UI</a>';
                    console.error('ReDoc initialization failed:', error);
                }
            });
        </script>
    </body>
    </html>
    """

@app.get("/")
def read_root():
    """根路径"""
    return {
        "message": "欢迎使用 FastAPI Web 应用",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "database": "connected"}

@app.get("/items/", response_model=List[schemas.Item])
def read_items(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """获取商品列表"""
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.get("/items/search", response_model=List[schemas.Item])
def search_items(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索商品"""
    items = crud.search_items(db, keyword=keyword, skip=skip, limit=limit)
    return items

@app.get("/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """获取单个商品"""
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="商品未找到")
    return db_item

@app.post("/items/", response_model=schemas.Item, status_code=201)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    """创建新商品"""
    return crud.create_item(db=db, item=item)

@app.put("/items/{item_id}", response_model=schemas.Item)
def update_item(
    item_id: int, 
    item: schemas.ItemUpdate, 
    db: Session = Depends(get_db)
):
    """更新商品信息"""
    db_item = crud.update_item(db=db, item_id=item_id, item=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="商品未找到")
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """删除商品"""
    success = crud.delete_item(db=db, item_id=item_id)
    if not success:
        raise HTTPException(status_code=404, detail="商品未找到")
    return {"message": "商品删除成功"}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
