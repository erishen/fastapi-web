#!/usr/bin/env bash

# 数据库初始化脚本 - 阿里云环境

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 切换到项目目录
cd "$PROJECT_DIR"

echo "========================================="
echo "FastAPI Web 数据库初始化脚本"
echo "========================================="
echo ""
echo "工作目录: $PWD"
echo ""

# 从 .env 读取配置（如果存在）
if [ -f .env ]; then
    echo "使用 .env 配置"
    # 安全方式读取配置，避免特殊字符问题
    export MYSQL_HOST=$(grep '^MYSQL_HOST=' .env | cut -d= -f2-)
    export MYSQL_PORT=$(grep '^MYSQL_PORT=' .env | cut -d= -f2-)
    export MYSQL_USER=$(grep '^MYSQL_USER=' .env | cut -d= -f2-)
    export MYSQL_PASSWORD=$(grep '^MYSQL_PASSWORD=' .env | cut -d= -f2-)
    export MYSQL_DATABASE=$(grep '^MYSQL_DATABASE=' .env | cut -d= -f2-)
    export REDIS_HOST=$(grep '^REDIS_HOST=' .env | cut -d= -f2-)
    export REDIS_PORT=$(grep '^REDIS_PORT=' .env | cut -d= -f2-)
    export REDIS_PASSWORD=$(grep '^REDIS_PASSWORD=' .env | cut -d= -f2-)
else
    echo "未找到配置文件，使用默认值"
fi

# 默认值
MYSQL_HOST=${MYSQL_HOST:-127.0.0.1}
MYSQL_PORT=${MYSQL_PORT:-3306}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-}
MYSQL_DATABASE=${MYSQL_DATABASE:-fastapi_web}
REDIS_HOST=${REDIS_HOST:-127.0.0.1}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD:-}

echo "数据库配置:"
echo "  主机: $MYSQL_HOST:$MYSQL_PORT"
echo "  用户: $MYSQL_USER"
echo "  数据库: $MYSQL_DATABASE"
echo ""

# 创建数据库
echo "创建数据库 $MYSQL_DATABASE ..."
mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD <<EOF
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 显示创建的数据库
SHOW DATABASES LIKE '$MYSQL_DATABASE';

-- 显示字符集信息
SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = '$MYSQL_DATABASE';
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 数据库 $MYSQL_DATABASE 创建成功"
else
    echo ""
    echo "✗ 数据库创建失败"
    exit 1
fi

# 测试连接
echo ""
echo "测试数据库连接..."
mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD -e "USE $MYSQL_DATABASE; SELECT '连接成功' AS status;"

if [ $? -eq 0 ]; then
    echo "✓ 数据库连接测试通过"
else
    echo "✗ 数据库连接测试失败"
    exit 1
fi

# 检查 Redis
echo ""
echo "检查 Redis 连接..."
if redis-cli -h $REDIS_HOST -p $REDIS_PORT -n 0 -a $REDIS_PASSWORD ping 2>/dev/null | grep -q PONG; then
    echo "✓ Redis 连接正常"
else
    echo "✗ Redis 连接失败"
    echo "  请检查 Redis 是否运行: systemctl status redis"
    echo "  或手动启动: systemctl start redis"
fi

echo ""
echo "========================================="
echo "初始化完成"
echo "========================================="
echo ""
echo "现在可以启动服务: make prod-up"
