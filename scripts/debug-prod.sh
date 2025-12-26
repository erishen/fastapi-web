#!/bin/bash

# 生产环境调试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "========================================="
echo "生产环境调试脚本"
echo "========================================="
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ 错误: .env 文件不存在"
    exit 1
fi

# 读取配置
PORT=$(grep '^PORT=' .env | cut -d= -f2-)
MYSQL_HOST=$(grep '^MYSQL_HOST=' .env | cut -d= -f2-)
MYSQL_PORT=$(grep '^MYSQL_PORT=' .env | cut -d= -f2-)
MYSQL_DATABASE=$(grep '^MYSQL_DATABASE=' .env | cut -d= -f2-)

echo "配置信息:"
echo "  端口: $PORT"
echo "  MySQL: $MYSQL_HOST:$MYSQL_PORT/$MYSQL_DATABASE"
echo ""

# 检查容器状态
echo "1️⃣  检查容器状态..."
docker compose -f docker-compose.prod.yml ps
echo ""

# 检查容器日志（最近 30 行）
echo "2️⃣  容器日志（最近 30 行）:"
docker compose -f docker-compose.prod.yml logs --tail=30 app
echo ""

# 检查端口监听
echo "3️⃣  端口监听状态:"
netstat -tuln | grep ":$PORT " || echo "端口 $PORT 未监听"
echo ""

# 测试 HTTP 响应
echo "4️⃣  测试 HTTP 响应:"
RESPONSE=$(curl -s http://localhost:$PORT/health 2>&1)
echo "原始响应: $RESPONSE"
echo ""

if echo "$RESPONSE" | grep -q "healthy"; then
    echo "✅ HTTP 响应正常"
else
    echo "❌ HTTP 响应异常"
fi
echo ""

# 进入容器测试
echo "5️⃣  容器内部测试:"
docker compose -f docker-compose.prod.yml exec -T app curl -s http://localhost:$PORT/health || echo "容器内部访问失败"
echo ""

# 检查网络模式
echo "6️⃣  网络配置:"
NETWORK_MODE=$(docker inspect fastapi-web-app --format='{{.HostConfig.NetworkMode}}' 2>/dev/null || echo "无法获取")
echo "  网络模式: $NETWORK_MODE"
echo ""

# 检查 MySQL 连接
echo "7️⃣  MySQL 连接测试:"
MYSQL_USER=$(grep '^MYSQL_USER=' .env | cut -d= -f2-)
MYSQL_PASSWORD=$(grep '^MYSQL_PASSWORD=' .env | cut -d= -f2-)

if mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD -e "USE $MYSQL_DATABASE; SELECT 1;" 2>/dev/null; then
    echo "✅ MySQL 连接正常"
else
    echo "❌ MySQL 连接失败"
fi
echo ""

echo "========================================="
echo "调试完成"
echo "========================================="
