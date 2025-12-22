# FastAPI Web 应用

一个基于 FastAPI 的商品管理系统，支持 Docker 容器化部署。

## 🚀 快速开始

### 启动应用

```bash
# 使用 Make（推荐）
make up

# 或使用脚本
./docker-start.sh up

# 或使用 Docker Compose
docker compose up -d
```

### 访问应用

- **API 文档**: http://localhost:8080/docs
- **应用首页**: http://localhost:8080

### 停止应用

```bash
make down
```

## 📁 项目结构

```
fastapi-web/
├── app/                    # 应用源代码
│   ├── routers/            # API 路由
│   ├── config.py           # 应用配置
│   ├── database.py         # 数据库连接
│   ├── models.py           # 数据模型
│   ├── schemas.py          # 数据验证
│   ├── security.py         # 安全认证
│   ├── redis_client.py     # Redis 客户端
│   ├── middleware.py       # 中间件
│   ├── exceptions.py       # 异常处理
│   ├── crud.py             # 数据库操作
│   ├── factory.py          # 应用工厂
│   └── main.py             # 应用入口
│
├── docs/                   # 文档
│   ├── DOCKER_SETUP.md     # Docker 部署指南
│   └── DOCKER_QUICK_START.md # Docker 快速参考
│
├── config/                 # 配置文件
│   ├── .env.example        # 环境变量示例
│   ├── .env.docker         # Docker 环境变量
│   └── nginx.conf          # Nginx 配置
│
├── scripts/                # 脚本文件
├── logs/                   # 日志目录
├── backups/                # 备份目录
├── ssl/                    # SSL 证书目录
│
├── Dockerfile              # Docker 镜像构建
├── docker compose.yml      # Docker Compose 配置
├── docker-start.sh         # Docker 启动脚本（Linux/macOS）
├── docker-start.bat        # Docker 启动脚本（Windows）
├── Makefile                # Make 命令
├── QUICK_REFERENCE.md      # 快速参考卡片
├── requirements.txt        # Python 依赖
└── .gitignore              # Git 忽略文件
```

## 🔧 常用命令

```bash
# 启动/停止
make up              # 启动所有服务
make down            # 停止所有服务
make restart         # 重启所有服务

# 查看状态
make ps              # 查看容器状态
make health          # 检查服务健康状态
make logs            # 查看实时日志

# 容器操作
make shell           # 进入应用容器
make db              # 进入数据库容器
make redis           # 进入 Redis 容器

# 数据库操作
make backup          # 备份数据库
make restore FILE=backups/xxx.sql  # 恢复数据库

# 其他
make build           # 重新构建镜像
make clean           # 清理容器和卷
make help            # 查看所有命令
```

## 🌐 服务访问

| 服务 | 地址 | 说明 |
|------|------|------|
| FastAPI 应用 | http://localhost:8080 | 主应用 |
| API 文档 | http://localhost:8080/docs | Swagger UI |
| Nginx 代理 | http://localhost:80 | 反向代理 |
| MySQL | localhost:3306 | 数据库 |
| Redis | localhost:6379 | 缓存 |

## 📋 数据库连接信息

### MySQL
```
主机: localhost
端口: 3306
用户名: root
密码: password
数据库: fastapi_web
```

### Redis
```
主机: localhost
端口: 6379
数据库: 0
```

## 🔐 环境配置

### 本地开发

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑环境变量
vim .env

# 重启应用使配置生效
make restart
```

### Docker 环境

Docker Compose 会自动使用 `config/.env.docker`

## 📦 依赖管理

### 主要依赖

- **FastAPI** - Web 框架
- **SQLAlchemy** - ORM
- **Pydantic** - 数据验证
- **Redis** - 缓存
- **PyMySQL** - MySQL 驱动
- **python-jose** - JWT 认证
- **passlib** - 密码加密

### 更新依赖

```bash
# 查看过期的包
pip list --outdated

# 更新所有包
pip install --upgrade -r requirements.txt
```

## 🐛 故障排查

### 应用无法启动

```bash
# 查看详细日志
docker compose logs app

# 检查依赖
docker compose exec app pip list
```

### 数据库连接失败

```bash
# 检查 MySQL 服务
docker compose ps mysql

# 测试连接
docker compose exec mysql mysql -uroot -ppassword -e "SELECT 1"
```

### Redis 连接失败

```bash
# 检查 Redis 服务
docker compose ps redis

# 测试连接
docker compose exec redis redis-cli ping
```

## 📚 文档

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - 常用命令速查表
- **[docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md)** - Docker 部署完整指南
- **[docs/DOCKER_QUICK_START.md](docs/DOCKER_QUICK_START.md)** - Docker 快速参考
- **[readme.md](readme.md)** - 项目原始文档

## 🚢 部署

### Docker 部署

```bash
# 构建镜像
docker compose build

# 启动服务
docker compose up -d

# 查看状态
docker compose ps
```

### 生产环境检查清单

- [ ] 修改所有默认密码
- [ ] 配置 SSL 证书
- [ ] 启用 HTTPS
- [ ] 配置备份策略
- [ ] 设置监控告警
- [ ] 配置日志收集
- [ ] 性能优化

## 📞 获取帮助

- 查看 **QUICK_REFERENCE.md** 中的常见问题
- 查看 **docs/DOCKER_SETUP.md** 中的故障排查
- 查看 **docs/DOCKER_QUICK_START.md** 中的快速参考

## 📚 相关资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)

## 📄 许可证

MIT License
