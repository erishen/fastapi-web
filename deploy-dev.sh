#!/bin/bash

# 本地开发环境启动脚本

set -e

echo "🚀 启动 FastAPI 开发环境..."

# 检查 .env.local 是否存在
if [ ! -f ".env.local" ]; then
    echo "❌ 错误: .env.local 文件不存在"
    echo "请先配置开发环境变量"
    exit 1
fi

# 检查宿主机 MySQL 是否运行
if ! mysqladmin ping -h 127.0.0.1 --silent 2>/dev/null; then
    echo "❌ 错误: MySQL 未运行"
    echo "请先启动 MySQL: brew services start mysql"
    exit 1
fi

# 检查宿主机 Redis 是否运行
if ! redis-cli ping >/dev/null 2>&1; then
    echo "❌ 错误: Redis 未运行"
    echo "请先启动 Redis: brew services start redis"
    exit 1
fi

# 复制开发环境配置
cp .env.local .env

# 检查数据库是否存在
echo "📋 检查数据库..."
DB_EXISTS=$(mysql -u root -p'Ls,(8888' -se "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'fastapi_web'" 2>/dev/null)

if [ -z "$DB_EXISTS" ]; then
    echo "📝 创建数据库..."
    mysql -u root -p'Ls,(8888' -e "CREATE DATABASE IF NOT EXISTS fastapi_web CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    echo "✅ 数据库创建成功"
else
    echo "✅ 数据库已存在"
fi

# 构建并启动
echo "🔨 构建 Docker 镜像..."
docker-compose build

echo "🚀 启动容器..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 显示服务状态
echo ""
echo "✅ 开发环境启动成功！"
echo ""
echo "📊 服务信息:"
docker-compose ps
echo ""
echo "📝 查看日志: docker-compose logs -f app"
echo "🌐 访问地址: http://localhost:8080"
echo "📖 API 文档: http://localhost:8080/docs"
echo ""
echo "停止服务: ./stop-dev.sh"
