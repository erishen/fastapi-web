# FastAPI Web 部署指南

## 本地开发（使用宿主机 MySQL 和 Redis）

### 前置条件
确保 Mac 上已安装并运行 MySQL 和 Redis：
```bash
# 检查 MySQL
brew services list | grep mysql
mysql.server status

# 检查 Redis
brew services list | grep redis
redis-cli ping
```

### 启动开发环境
```bash
# 复制开发环境配置
cp .env.local .env

# 启动 FastAPI 容器
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

### 数据库初始化
首次运行需要创建数据库和表：
```bash
# 连接到 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE IF NOT EXISTS fastapi_web CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 阿里云生产部署（共享 WordPress MySQL 和 Redis）

### 资源配置（2核2G 机器）

**内存分配:**
- FastAPI 应用: 512MB (docker limit)
- WordPress (PHP + Apache): ~600MB
- MySQL: 256MB buffer pool
- Redis: 128MB max memory
- 系统预留: ~200MB
- **总计: ~1.7GB** ✅

### MySQL 配置优化

在服务器的 MySQL 配置文件中添加 (`/etc/mysql/mysql.conf.d/mysqld.cnf` 或 `/etc/my.cnf`):

```ini
[mysqld]
# 内存限制
innodb_buffer_pool_size = 256M
innodb_log_file_size = 64M
innodb_flush_log_at_trx_commit = 2

# 连接数限制
max_connections = 100
max_connect_errors = 1000000

# 性能优化
innodb_flush_method = O_DIRECT
innodb_file_per_table = 1

# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

重启 MySQL:
```bash
sudo systemctl restart mysql
```

### Redis 配置优化

修改 Redis 配置文件 (`/etc/redis/redis.conf`):

```conf
# 内存限制
maxmemory 128mb

# 内存淘汰策略（移除最久未使用的键）
maxmemory-policy allkeys-lru

# 持久化（可选，根据需求调整）
appendonly yes
appendfsync everysec
```

重启 Redis:
```bash
sudo systemctl restart redis
```

### 部署步骤

1. **上传代码到服务器**
```bash
# 在服务器上
cd /var/www
git clone <your-repo-url> fastapi-web
cd fastapi-web
```

2. **配置生产环境**
```bash
# 复制生产环境配置
cp .env.production .env

# 编辑配置文件
nano .env
```

**必须修改的配置:**
```bash
# 生成 SECRET_KEY
openssl rand -hex 32
# 将结果填入 SECRET_KEY

# 生成 NEXTAUTH_SECRET
openssl rand -hex 32
# 将结果填入 NEXTAUTH_SECRET

# 生成管理员密码哈希
python3 generate_password_hash.py <your-strong-password>
# 将结果填入 ADMIN_PASSWORD_HASH

# 修改数据库密码（确保与 MySQL 配置一致）
MYSQL_ROOT_PASSWORD=<your-root-password>
MYSQL_PASSWORD=<your-password>

# 设置 Redis 密码（确保与 Redis 配置一致）
REDIS_PASSWORD=<your-redis-password>

# 设置前端实际域名
WEB_URL=https://your-domain.com
ADMIN_URL=https://admin.your-domain.com
```

3. **创建数据库**
```bash
mysql -u root -p
```
```sql
CREATE DATABASE IF NOT EXISTS fastapi_web CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fastapi_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON fastapi_web.* TO 'fastapi_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

4. **设置 Redis 密钥**（如果 Redis 没有设置密码）
```bash
# 编辑 Redis 配置
sudo nano /etc/redis/redis.conf

# 添加或修改
requirepass your-redis-password

# 重启 Redis
sudo systemctl restart redis
```

5. **构建并启动容器**
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

6. **验证部署**
```bash
# 健康检查
curl http://localhost:8080/health

# 访问 API 文档
curl http://localhost:8080/docs
```

### Nginx 反向代理配置

在 Nginx 配置中添加 FastAPI 服务:

```nginx
upstream fastapi_backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 限制请求体大小
    client_max_body_size 10M;
}
```

重载 Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 监控和维护

**查看容器资源使用:**
```bash
docker stats fastapi-web-app
```

**查看日志:**
```bash
# 应用日志
docker-compose logs -f app

# 查看最近 100 行
docker-compose logs --tail=100 app
```

**重启服务:**
```bash
docker-compose restart app
```

**更新代码:**
```bash
git pull
docker-compose up -d --build
```

### 安全建议

1. **防火墙配置**
```bash
# 只允许特定端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

2. **定期备份数据库**
```bash
# 备份脚本
#!/bin/bash
mysqldump -u root -p fastapi_web > /backup/fastapi_web_$(date +%Y%m%d_%H%M%S).sql

# 添加到 crontab（每天凌晨 2 点备份）
0 2 * * * /path/to/backup_script.sh
```

3. **更新和打补丁**
```bash
# 定期更新系统和 Docker
sudo apt update && sudo apt upgrade -y
docker-compose pull
docker-compose up -d
```

## 故障排查

### MySQL 连接失败
```bash
# 检查 MySQL 是否运行
sudo systemctl status mysql

# 检查端口
netstat -tlnp | grep 3306

# 测试连接
mysql -h 127.0.0.1 -u fastapi_user -p fastapi_web
```

### Redis 连接失败
```bash
# 检查 Redis 是否运行
sudo systemctl status redis

# 测试连接
redis-cli -a your-password ping
```

### 容器内存不足
```bash
# 检查容器内存使用
docker stats

# 查看系统内存
free -h

# 如果内存不足，考虑：
# 1. 调整 MySQL innodb_buffer_pool_size
# 2. 调整 Redis maxmemory
# 3. 升级服务器配置
```

## 性能优化建议

1. **启用 Gzip 压缩** (Nginx)
2. **配置 CDN** 加速静态资源
3. **使用缓存** 减少数据库查询
4. **监控资源使用**，及时扩容
5. **定期清理日志文件**
