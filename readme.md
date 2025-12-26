# FastAPI Web 项目

一个基于 FastAPI 的商品管理系统。

## 快速开始

### 本地开发环境

确保 Mac 上已安装并运行 MySQL 和 Redis：

```bash
# 安装 MySQL（如果未安装）
brew install mysql
brew services start mysql

# 安装 Redis（如果未安装）
brew install redis
brew services start redis
```

启动开发环境：

```bash
# 启动服务
./deploy-dev.sh

# 停止服务
./stop-dev.sh
```

访问地址：
- API: http://localhost:8080
- API 文档: http://localhost:8080/docs

### 生产环境部署

详细部署指南请查看 [DEPLOYMENT.md](./DEPLOYMENT.md)

```bash
# 在服务器上运行
sudo ./deploy-prod.sh
```

## 项目结构

```
fastapi-web/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic schemas
│   ├── security.py        # 安全相关（JWT、认证）
│   ├── security_headers.py # 安全响应头
│   ├── middleware.py      # 中间件（速率限制）
│   ├── config.py          # 配置管理
│   └── factory.py         # 应用工厂
├── scripts/               # 脚本文件
├── logs/                  # 日志文件
├── docker-compose.yml     # Docker Compose 配置
├── Dockerfile            # Docker 镜像配置
├── .env.local            # 本地开发环境变量
├── .env.production       # 生产环境变量模板
├── deploy-dev.sh         # 开发环境部署脚本
├── stop-dev.sh           # 停止开发环境脚本
├── deploy-prod.sh        # 生产环境部署脚本
└── DEPLOYMENT.md         # 详细部署文档
```

## 环境变量

### 本地开发 (.env.local)
使用宿主机的 MySQL 和 Redis，无需独立数据库。

### 生产环境 (.env.production)
- 连接到服务器上的 MySQL（与 WordPress 共享）
- 连接到服务器上的 Redis（与 WordPress 共享）
- 必须配置安全密钥和密码哈希

## 资源配置

### 本地开发
- FastAPI 容器: 256-512MB
- 使用宿主机 MySQL 和 Redis

### 生产环境（2核2G 机器）
- FastAPI 应用: 512MB (docker limit)
- MySQL buffer pool: 256MB
- Redis max memory: 128MB
- WordPress (PHP): ~600MB
- 系统预留: ~200MB
- **总计: ~1.7GB** ✅

## 安全特性

- ✅ JWT 认证（强制强密钥）
- ✅ NextAuth token 验证
- ✅ 多级速率限制
- ✅ 安全响应头（CSP、HSTS、X-Frame-Options 等）
- ✅ 密码哈希（bcrypt）
- ✅ CORS 严格限制
- ✅ 环境感知错误处理
- ✅ 审计日志

## 常用命令

```bash
# 查看日志
docker-compose logs -f app

# 重启服务
docker-compose restart app

# 进入容器
docker-compose exec app bash

# 查看资源使用
docker stats fastapi-web-app

# 生成密码哈希
python generate_password_hash.py <password>

# 生成安全密钥
openssl rand -hex 32
```

## 故障排查

### MySQL 连接失败
```bash
# 检查 MySQL 是否运行
mysqladmin ping -h 127.0.0.1

# 检查数据库是否存在
mysql -u root -p -e "SHOW DATABASES;"
```

### Redis 连接失败
```bash
# 检查 Redis 是否运行
redis-cli ping
```

### 容器问题
```bash
# 查看容器日志
docker-compose logs app

# 重新构建
docker-compose up -d --build
```

## 维护建议

1. 定期备份数据库
2. 监控资源使用情况
3. 及时更新依赖包
4. 定期查看日志
5. 配置日志轮转

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License
