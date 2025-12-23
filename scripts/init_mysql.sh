#!/bin/bash

# MySQL Docker 初始化脚本
# 用于在 MySQL 容器首次启动时创建用户和权限

echo "🗄️  MySQL Docker 初始化脚本"
echo "============================="

# 等待 MySQL 服务完全启动
echo "⏳ 等待 MySQL 服务启动..."
sleep 10

# 创建应用用户并授权
echo "👤 创建应用用户并设置权限..."

mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
-- 创建应用用户（允许从任何主机连接）
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'%' IDENTIFIED BY '$MYSQL_PASSWORD';

-- 授予应用用户所有权限
GRANT ALL PRIVILEGES ON $MYSQL_DATABASE.* TO '$MYSQL_USER'@'%';

-- 允许 root 用户从容器网络连接（用于健康检查）
-- 注意：生产环境应该限制 root 访问
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示用户权限（用于调试）
SELECT User, Host FROM mysql.user WHERE User IN ('$MYSQL_USER', 'root');
EOF

if [ $? -eq 0 ]; then
    echo "✅ 用户权限设置成功"
    echo "   - 用户: $MYSQL_USER (允许所有主机连接)"
    echo "   - 数据库: $MYSQL_DATABASE"
else
    echo "❌ 用户权限设置失败"
    exit 1
fi

echo ""
echo "🎉 MySQL Docker 初始化完成！"
echo "📝 应用现在可以连接到 MySQL 数据库"