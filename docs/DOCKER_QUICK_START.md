# FastAPI Web Docker 快速启动指南

## 快速开始（3 步）

### 1. 启动服务
```bash
# Linux/macOS
./docker-start.sh up

# Windows
docker-start.bat up

# 或使用 Makefile
make up
```

### 2. 验证服务
```bash
# 查看服务状态
docker compose ps

# 检查应用健康状态
curl http://localhost:8080/health

# 访问 API 文档
# 浏览器打开: http://localhost:8080/docs
```

### 3. 停止服务
```bash
./docker-start.sh down
# 或
make down
```

---

## 常用命令速查表

### 使用 Shell 脚本（Linux/macOS）

| 命令 | 说明 |
|------|------|
| `./docker-start.sh up` | 启动所有服务 |
| `./docker-start.sh up --build` | 重新构建并启动 |
| `./docker-start.sh up --foreground` | 前台运行（显示日志） |
| `./docker-start.sh down` | 停止所有服务 |
| `./docker-start.sh restart` | 重启所有服务 |
| `./docker-start.sh logs` | 查看实时日志 |
| `./docker-start.sh status` | 查看服务状态 |
| `./docker-start.sh shell` | 进入应用容器 |
| `./docker-start.sh db` | 进入数据库容器 |
| `./docker-start.sh redis` | 进入 Redis 容器 |
| `./docker-start.sh backup` | 备份数据库 |
| `./docker-start.sh restore <file>` | 恢复数据库 |

### 使用 Makefile

| 命令 | 说明 |
|------|------|
| `make up` | 启动所有服务 |
| `make up-build` | 重新构建并启动 |
| `make up-foreground` | 前台运行 |
| `make down` | 停止所有服务 |
| `make restart` | 重启所有服务 |
| `make logs` | 查看实时日志 |
| `make logs-app` | 查看应用日志 |
| `make status` | 查看服务状态 |
| `make health` | 检查服务健康状态 |
| `make shell` | 进入应用容器 |
| `make db` | 进入数据库容器 |
| `make redis` | 进入 Redis 容器 |
| `make mysql-cli` | 进入 MySQL 命令行 |
| `make redis-cli` | 进入 Redis 命令行 |
| `make backup` | 备份数据库 |
| `make restore FILE=backups/xxx.sql` | 恢复数据库 |
| `make clean` | 清理容器和卷 |
| `make info` | 显示服务信息 |

### 使用 Docker Compose 直接命令

```bash
# 启动
docker compose up -d

# 停止
docker compose down

# 查看日志
docker compose logs -f

# 查看状态
docker compose ps

# 进入容器
docker compose exec app bash
docker compose exec mysql bash
docker compose exec redis sh
```

---

## 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| FastAPI 应用 | http://localhost:8080 | 主应用 |
| API 文档 | http://localhost:8080/docs | Swagger UI |
| Nginx 代理 | http://localhost:80 | 反向代理 |
| MySQL | localhost:3307 | 数据库 |
| Redis | localhost:6380 | 缓存 |

---

## 数据库连接信息

### MySQL
```
主机: localhost
端口: 3307
用户名: root
密码: password
数据库: fastapi_web
```

### Redis
```
主机: localhost
端口: 6380
密码: redispassword
数据库: 0
```

---

## 常见操作

### 查看日志

```bash
# 查看所有服务日志
make logs

# 查看应用日志
make logs-app

# 查看最后 100 行
docker compose logs --tail=100 app

# 实时查看特定服务
docker compose logs -f mysql
```

### 进入容器

```bash
# 进入应用容器
make shell

# 进入数据库容器
make db

# 进入 Redis 容器
make redis

# 进入 MySQL 命令行
make mysql-cli
```

### 数据库操作

```bash
# 备份数据库
make backup

# 恢复数据库
make restore FILE=backups/mysql_backup_20240101_120000.sql

# 进入 MySQL 命令行
make mysql-cli

# 查看数据库
mysql> SHOW DATABASES;
mysql> USE fastapi_web;
mysql> SHOW TABLES;
```

### Redis 操作

```bash
# 进入 Redis 命令行
make redis-cli

# 查看所有键
redis> KEYS *

# 获取键值
redis> GET key_name

# 删除键
redis> DEL key_name

# 清空数据库
redis> FLUSHDB
```

---

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
docker compose logs app

# 检查端口是否被占用
lsof -i :8080
lsof -i :3307
lsof -i :6380

# 清理并重新启动
make clean
make up
```

### 数据库连接失败

```bash
# 检查 MySQL 服务
docker compose ps mysql

# 查看 MySQL 日志
docker compose logs mysql

# 进入 MySQL 容器测试
docker compose exec mysql mysql -uroot -ppassword -e "SELECT 1"
```

### Redis 连接失败

```bash
# 检查 Redis 服务
docker compose ps redis

# 测试 Redis 连接
docker compose exec redis redis-cli ping
```

### 应用无法访问

```bash
# 检查应用是否运行
docker compose ps app

# 测试应用健康状态
curl http://localhost:8080/health

# 查看应用日志
docker compose logs -f app
```

---

## 环境变量配置

### 创建环境配置文件

```bash
# 创建 .env.docker 文件
cat > .env.docker << EOF
# 应用配置
EXPOSE_PORT=8080
SECRET_KEY=your-secret-key-change-this-in-production
LOG_LEVEL=info

# MySQL 数据库配置
MYSQL_PASSWORD=your-mysql-password
MYSQL_EXPOSE_PORT=3307

# Redis 缓存配置
REDIS_PASSWORD=your-redis-password
REDIS_EXPOSE_PORT=6380
REDIS_URL=redis://:your-redis-password@redis:6379/0
EOF
```

**注意**: Docker Compose 会自动读取 `.env.docker` 文件中的变量。

---

## 性能优化

### 增加数据库连接池

编辑 `.env.docker`:
```
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

### 增加 Redis 缓存时间

编辑 `.env.docker`:
```
CACHE_EXPIRE_SECONDS=7200
```

### 调整 Nginx 工作进程

编辑 `nginx.conf`:
```nginx
worker_processes auto;
worker_connections 2048;
```

---

## 生产环境部署

### 1. 修改密钥和密码

编辑 `docker compose.yml`:
```yaml
environment:
  - SECRET_KEY=your-production-secret-key
  - MYSQL_ROOT_PASSWORD=strong-password
```

### 2. 启用 HTTPS

1. 获取 SSL 证书
2. 将证书放在 `ssl/` 目录
3. 取消注释 `nginx.conf` 中的 HTTPS 配置

### 3. 配置备份

```bash
# 定期备份数据库
0 2 * * * cd /path/to/fastapi-web && make backup
```

### 4. 监控和告警

```bash
# 定期检查服务健康状态
*/5 * * * * curl -f http://localhost:8080/health || alert
```

---

## 清理资源

```bash
# 停止并删除容器
make down

# 删除卷（谨慎操作）
docker compose down -v

# 清理未使用的 Docker 资源
make prune

# 完全清理
docker system prune -a
```

---

## 获取帮助

```bash
# 查看脚本帮助
./docker-start.sh --help

# 查看 Makefile 帮助
make help

# 查看 Docker Compose 帮助
docker compose --help
```

---

## 提示

- 首次启动可能需要 1-2 分钟来初始化数据库
- 修改 `.env.docker` 后需要重启服务
- 定期备份数据库以防数据丢失
- 生产环境务必修改默认密码
- 使用 `make health` 检查服务健康状态
