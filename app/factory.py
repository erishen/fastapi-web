from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .config import settings
from .middleware import setup_middleware
from .exceptions import setup_exception_handlers
from .security_headers import setup_security_headers
from .routers import items, system, auth, redis, doc_logs
from .redis_client import redis_client
from . import models
from .database import engine

def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    # 创建数据表
    models.Base.metadata.create_all(bind=engine)

    # 创建应用实例（禁用默认的 docs，使用自定义的）
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url=None,  # 禁用默认 docs，使用自定义路由
        redoc_url=None,  # 禁用默认 redoc，使用自定义路由
        openapi_url=settings.openapi_url,
        debug=settings.debug
    )

    # 设置中间件（顺序很重要）
    setup_security_headers(app)  # 安全响应头必须最先
    setup_middleware(app)  # CORS 和速率限制

    # 设置异常处理器
    setup_exception_handlers(app)

    # 应用启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动时的初始化"""
        if settings.debug:
            print("🚀 FastAPI 应用启动中...")

        # 连接 Redis
        await redis_client.connect()

        # 初始化示例商品数据（从配置文件读取）
        from .database import SessionLocal
        from . import models
        import json
        import os

        db = SessionLocal()
        try:
            # 检查是否已有商品数据
            existing_items = db.query(models.Item).count()
            if existing_items == 0:
                # 读取示例商品配置文件
                sample_data_path = os.path.join(os.path.dirname(__file__), "data", "sample_items.json")

                if os.path.exists(sample_data_path):
                    with open(sample_data_path, 'r', encoding='utf-8') as f:
                        sample_config = json.load(f)

                    # 检查是否启用初始化
                    if sample_config.get("enabled", True):
                        print("📦 初始化示例商品数据...")

                        items_data = sample_config.get("items", [])
                        sample_items = []

                        for item_data in items_data:
                            # 转换布尔值为整数（MySQL兼容）
                            is_offer_int = 1 if item_data.get("is_offer") else 0

                            sample_items.append(models.Item(
                                name=item_data["name"],
                                description=item_data.get("description"),
                                price=item_data["price"],
                                is_offer=is_offer_int
                            ))

                        # 批量插入
                        for item in sample_items:
                            db.add(item)

                        db.commit()
                        print(f"✓ 成功初始化 {len(sample_items)} 个示例商品")
                    else:
                        print("ℹ️  示例商品初始化已在配置中禁用")
                else:
                    print(f"⚠️  示例商品配置文件不存在: {sample_data_path}")
            else:
                print(f"✓ 数据库中已有 {existing_items} 个商品，跳过初始化")

        except Exception as e:
            db.rollback()
            print(f"✗ 初始化示例商品失败: {e}")
        finally:
            db.close()

        if settings.debug:
            print("✅ 应用启动完成")

    # 应用关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时的清理"""
        if settings.debug:
            print("🛑 FastAPI 应用关闭中...")

        # 断开 Redis 连接
        await redis_client.disconnect()

        if settings.debug:
            print("✅ 应用关闭完成")

    # 注册路由
    app.include_router(system.router)
    app.include_router(auth.router)  # 认证路由
    app.include_router(items.router)
    app.include_router(redis.router)  # Redis 路由
    app.include_router(doc_logs.router)  # 文档日志路由

    # 自定义 Swagger UI 页面
    @app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
    async def custom_swagger_ui():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FastAPI Web Application - API Documentation</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css">
            <style>
                html {
                    box-sizing: border-box;
                    overflow: -moz-scrollbars-vertical;
                    overflow-y: scroll;
                }
                *, *:before, *:after {
                    box-sizing: inherit;
                }
                body {
                    margin: 0;
                    padding: 0;
                }
            </style>
            <script>
                // 阻止 source map 加载请求
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    const url = args[0];
                    if (typeof url === 'string' && url.includes('.map')) {
                        console.log('Blocking source map request:', url);
                        return Promise.reject(new Error('Source map blocked'));
                    }
                    return originalFetch.apply(this, args);
                };
            </script>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
            <script>
                window.onload = function() {
                    const ui = SwaggerUIBundle({
                        url: '/openapi.json',
                        dom_id: '#swagger-ui',
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIBundle.presets.standalone
                        ],
                        layout: "BaseLayout",
                        deepLinking: true,
                        showExtensions: true,
                        showCommonExtensions: true,
                        defaultModelsExpandDepth: 1,
                        defaultModelExpandDepth: 1,
                        tryItOutEnabled: true,
                        filter: true,
                    });
                }
            </script>
        </body>
        </html>
        """

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
                .error {
                    text-align: center;
                    padding: 20px;
                    max-width: 600px;
                    margin: 50px auto;
                }
                .error a {
                    color: #32329f;
                    text-decoration: underline;
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
                        loading.innerHTML = `
                            <div class="error">
                                <h2>ReDoc 加载失败</h2>
                                <p>如果您看到此错误，可能是浏览器安全策略限制导致的。</p>
                                <p>请尝试以下方案：</p>
                                <ul style="text-align: left;">
                                    <li>刷新页面重试</li>
                                    <li>使用 <a href="/docs">Swagger UI</a> (推荐)</li>
                                    <li>清除浏览器缓存后重试</li>
                                </ul>
                                <p style="margin-top: 20px; color: #999;">
                                    错误详情: ${error.message}
                                </p>
                            </div>
                        `;
                        if (typeof console !== 'undefined') {
                            console.error('ReDoc initialization failed:', error);
                        }
                    }
                });
            </script>
        </body>
        </html>
        """

    return app