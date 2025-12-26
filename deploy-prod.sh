#!/bin/bash

# 生产环境部署脚本（阿里云）

set -e

echo "🚀 开始部署 FastAPI 生产环境..."

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 root 权限运行: sudo ./deploy-prod.sh"
    exit 1
fi

# 检查 .env.production 是否存在
if [ ! -f ".env.production" ]; then
    echo "❌ 错误: .env.production 文件不存在"
    echo "请先配置生产环境变量"
    exit 1
fi

# 复制生产环境配置
cp .env.production .env

echo "⚠️  请确认以下配置正确:"
echo "  - MySQL 密码已设置"
echo "  - Redis 密码已设置"
echo "  - SECRET_KEY 已生成"
echo "  - NEXTAUTH_SECRET 已生成"
echo "  - ADMIN_PASSWORD_HASH 已生成"
echo "  - 前端域名已配置"
echo ""
read -p "确认配置正确并继续部署? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 部署已取消"
    exit 1
fi

# 检查 MySQL 是否运行
echo "📋 检查 MySQL 服务..."
if ! systemctl is-active --quiet mysql; then
    echo "❌ MySQL 未运行，正在启动..."
    systemctl start mysql
fi

# 检查 Redis 是否运行
echo "📋 检查 Redis 服务..."
if ! systemctl is-active --quiet redis; then
    echo "❌ Redis 未运行，正在启动..."
    systemctl start redis
fi

# 检查数据库是否存在
echo "📋 检查数据库..."
source .env
DB_EXISTS=$(mysql -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -se "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '$MYSQL_DATABASE'" 2>/dev/null)

if [ -z "$DB_EXISTS" ]; then
    echo "📝 创建数据库和用户..."
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
CREATE DATABASE IF NOT EXISTS $MYSQL_DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON $MYSQL_DATABASE.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    echo "✅ 数据库创建成功"
else
    echo "✅ 数据库已存在"
fi

# 构建 Docker 镜像
echo "🔨 构建 Docker 镜像..."
docker-compose build --no-cache

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down

# 启动新容器
echo "🚀 启动新容器..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🏥 健康检查..."
HEALTH_CHECK=$(curl -s http://localhost:8080/health || echo "failed")

if [ "$HEALTH_CHECK" != "OK" ]; then
    echo "⚠️  健康检查失败，查看日志..."
    docker-compose logs --tail=50 app
    exit 1
fi

echo ""
echo "✅ 生产环境部署成功！"
echo ""
echo "📊 服务状态:"
docker-compose ps
echo ""
echo "📖 API 文档: http://localhost:8080/docs"
echo "📝 查看日志: docker-compose logs -f app"
echo ""
echo "下一步:"
echo "  1. 配置 Nginx 反向代理 (参考 DEPLOYMENT.md)"
echo "  2. 设置 SSL 证书"
echo "  3. 配置防火墙规则"
