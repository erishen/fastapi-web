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

# 从环境变量获取配置
APP_USER=${MYSQL_USER:-fastapi_user}
APP_PASSWORD=${MYSQL_PASSWORD:-fastapi_password}
DATABASE=${MYSQL_DATABASE:-fastapi_web}

mysql -u root -p"${MYSQL_ROOT_PASSWORD:-root_password}" << EOF
-- 创建默认应用用户（始终创建）
CREATE USER IF NOT EXISTS 'fastapi_user'@'%' IDENTIFIED BY 'fastapi_password';

-- 如果指定了不同的用户且不是 root，则创建该用户
-- 注意：MySQL 官方镜像不允许 MYSQL_USER=root，所以这里跳过 root 用户的创建
-- 但 root 用户已经存在并有权限
CREATE USER IF NOT EXISTS '${APP_USER}'@'%' IDENTIFIED BY '${APP_PASSWORD}';

-- 授予权限
GRANT ALL PRIVILEGES ON ${DATABASE}.* TO 'fastapi_user'@'%';
GRANT ALL PRIVILEGES ON ${DATABASE}.* TO '${APP_USER}'@'%';

-- 允许 root 用户从容器网络连接（用于健康检查）
-- 注意：生产环境应该限制 root 访问
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示用户权限（用于调试）
SELECT User, Host FROM mysql.user WHERE User IN ('fastapi_user', '${APP_USER}', 'root');
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