from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .config import settings
from .middleware import setup_middleware
from .exceptions import setup_exception_handlers
from .routers import items, system
from . import models
from .database import engine

def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    
    # 创建数据表
    models.Base.metadata.create_all(bind=engine)
    
    # 创建应用实例
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        debug=settings.debug
    )
    
    # 设置中间件
    setup_middleware(app)
    
    # 设置异常处理器
    setup_exception_handlers(app)
    
    # 注册路由
    app.include_router(system.router)
    app.include_router(items.router)
    
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
    
    return app