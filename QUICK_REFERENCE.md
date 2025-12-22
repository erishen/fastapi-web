# 快速参考

## 启动/停止

```bash
make up              # 启动所有服务
make down            # 停止所有服务
make restart         # 重启所有服务
```

## 查看状态

```bash
docker compose ps   # 查看容器状态
make logs           # 查看实时日志
make health         # 检查服务健康状态
```

## 进入容器

```bash
make shell          # 进入应用容器
make db             # 进入数据库容器
make redis          # 进入 Redis 容器
make mysql-cli      # 进入 MySQL 命令行
make redis-cli      # 进入 Redis 命令行
```

## 数据库操作

```bash
make backup         # 备份数据库
make restore FILE=backups/mysql_backup_xxx.sql  # 恢复数据库
```

## 其他命令

```bash
make build          # 重新构建镜像
make clean          # 清理容器和卷
make help           # 查看所有命令
make info           # 显示服务信息
```

## 访问应用

- API 文档: http://localhost:8080/docs
- 应用首页: http://localhost:8080
- Nginx: http://localhost:80

## 数据库连接

```
MySQL:  localhost:3306 (root/password)
Redis:  localhost:6379
```

## 常见问题

### 应用无法启动
```bash
docker compose logs app
```

### 数据库连接失败
```bash
docker compose exec mysql mysql -uroot -ppassword -e "SELECT 1"
```

### Redis 连接失败
```bash
docker compose exec redis redis-cli ping
```

### 端口被占用
修改 docker compose.yml 中的端口映射，例如: "8081:8080"
