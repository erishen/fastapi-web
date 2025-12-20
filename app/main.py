from .factory import create_app
from .config import settings
import uvicorn

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level
    )
