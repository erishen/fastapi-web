# FastAPI Web Docker 部署指南

## 项目结构

```
fastapi-web/
├── docker compose.yml      # Docker Compose 配置
├── Dockerfile              # FastAPI 应用镜像
├── .dockerignore           # Docker 构建忽略文件
├── .env.docker             # Docker 环境变量
├── app/                    # 应用源代码
├── scripts/                # 初始化脚本
└── logs/                   # 应用日志目录
```

## 服务组成

- **FastAPI App**: 主应用服务 (端口 8080)
- **MySQL**: 数据库服务 (端口 3307)
- **Redis**: 缓存服务 (端口 6380)

## 快速开始

### 1. 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 2GB 可用内存

### 2. 启动服务

```bash
# 进入项目目录
cd fastapi-web

# 构建并启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看应用日志
docker compose logs -f app
```

### 3. 验证服务

```bash
# 检查 FastAPI 应用
curl http://localhost:8080/health

# 查看 API 文档
# 浏览器访问: http://localhost:8080/docs

# 检查 MySQL
docker compose exec mysql mysql -uroot -ppassword -e "SELECT 1"

# 检查 Redis
docker compose exec redis redis-cli ping
```

## 常用命令

### 启动/停止服务

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 停止并删除数据卷
docker compose down -v

# 重启服务
docker compose restart

# 重启特定服务
docker compose restart app
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs app
docker compose logs mysql
docker compose logs redis

# 实时查看日志
docker compose logs -f app

# 查看最后 100 行日志
docker compose logs --tail=100 app
```

### 执行命令

```bash
# 进入应用容器
docker compose exec app bash

# 进入 MySQL 容器
docker compose exec mysql bash

# 进入 Redis 容器
docker compose exec redis sh

# 在应用容器中运行 Python 命令
docker compose exec app python -c "import app; print(app.__version__)"
```

### 数据库操作

```bash
# 连接 MySQL
docker compose exec mysql mysql -uroot -ppassword fastapi_web

# 备份数据库
docker compose exec mysql mysqldump -uroot -ppassword fastapi_web > backup.sql

# 恢复数据库
docker compose exec -T mysql mysql -uroot -ppassword fastapi_web < backup.sql

# 查看 Redis 数据
docker compose exec redis redis-cli
# 在 Redis CLI 中执行命令
# > KEYS *
# > GET key_name
```

## 环境配置

### 修改环境变量

编辑 `docker compose.yml` 中的 `environment` 部分或创建 `.env` 文件：

```bash
# 创建 .env.docker 文件
cat > .env.docker << EOF
# 应用配置
EXPOSE_PORT=8080
SECRET_KEY=your-production-secret-key
LOG_LEVEL=info

# MySQL 数据库配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=fastapi_web
MYSQL_EXPOSE_PORT=3307

# Redis 缓存配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0
REDIS_EXPOSE_PORT=6380
REDIS_URL=redis://:your-redis-password@redis:6379/0
EOF
```

### 生产环境配置

1. **修改密钥**
   ```yaml
   environment:
     - SECRET_KEY=your-very-secure-secret-key-here
   ```

2. **启用 HTTPS**
   使用外部反向代理（如 Nginx、Caddy 或 Traefik）处理 HTTPS

3. **配置数据库密码**
   ```yaml
   environment:
     - MYSQL_ROOT_PASSWORD=strong-password
   ```

4. **配置 Redis 密码**
   ```yaml
   # 默认密码: redispassword
   # 如需修改，在环境变量中设置 REDIS_PASSWORD
   redis:
     environment:
       REDIS_PASSWORD: ${REDIS_PASSWORD:-redispassword}
     command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redispassword}
   ```

   **连接示例：**
   ```bash
   # 使用密码连接
   redis-cli -h localhost -p 6380 -a redispassword

   # 或在 redis-cli 中认证
   redis-cli -h localhost -p 6380
   AUTH redispassword
   ```

## 性能优化

### 1. 数据库连接池

在 `.env.docker` 中调整：
```
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### 2. Redis 缓存

```
CACHE_EXPIRE_SECONDS=3600
```

### 3. 应用层缓存

在 FastAPI 应用中配置缓存：
```python
# 使用 Redis 缓存装饰器
from app.redis_client import cache_result

@cache_result("api_response", expire=3600)
async def get_data():
    # 缓存 1 小时
    pass
```

## 故障排查

### 应用无法连接数据库

```bash
# 检查 MySQL 服务状态
docker compose ps mysql

# 查看 MySQL 日志
docker compose logs mysql

# 测试连接
docker compose exec app python -c "from app.database import engine; engine.connect()"
```

### Redis 连接失败

```bash
# 检查 Redis 服务
docker compose ps redis

# 测试 Redis 连接
docker compose exec redis redis-cli ping
```

### 应用启动失败

```bash
# 查看详细日志
docker compose logs app

# 进入容器调试
docker compose exec app bash
```

### 端口被占用

```bash
# 查看占用的端口
lsof -i :8080
lsof -i :3307
lsof -i :6380

# 修改 docker compose.yml 中的端口映射
# 例如: "8081:8080" 将容器的 8080 映射到主机的 8081
```

## 数据持久化

所有数据都存储在 Docker 卷中：

```bash
# 查看卷
docker volume ls | grep fastapi

# 检查卷位置
docker volume inspect fastapi-web_mysql_data

# 备份卷
docker run --rm -v fastapi-web_mysql_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/mysql_backup.tar.gz -C /data .
```

## 清理资源

```bash
# 删除停止的容器
docker compose down

# 删除未使用的镜像
docker image prune

# 删除未使用的卷
docker volume prune

# 完全清理（谨慎操作）
docker compose down -v
docker system prune -a
```

## 监控和日志

### 查看容器资源使用

```bash
docker stats fastapi-web-app
docker stats fastapi-mysql
docker stats fastapi-redis
```

### 配置日志驱动

在 `docker compose.yml` 中添加：

```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 扩展和自定义

### 添加新服务

在 `docker compose.yml` 中添加新服务：

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
    networks:
      - fastapi-network
```

### 自定义 Dockerfile

修改 `Dockerfile` 以添加额外的依赖或配置。

## 安全建议

1. **不要在生产环境使用默认密码**
2. **使用强密钥和密码**
3. **启用 HTTPS**
4. **限制网络访问**
5. **定期备份数据**
6. **更新镜像和依赖**
7. **使用私有镜像仓库**

## 参考资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Nginx 文档](https://nginx.org/en/docs/)
