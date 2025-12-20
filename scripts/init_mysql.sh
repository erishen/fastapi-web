#!/bin/bash

# MySQL 数据库初始化脚本

echo "🗄️  MySQL 数据库初始化脚本"
echo "=========================="

# 检查 MySQL 是否运行
if ! pgrep -x "mysqld" > /dev/null; then
    echo "❌ MySQL 服务未运行，请先启动 MySQL"
    echo "💡 启动方法："
    echo "   - macOS: brew services start mysql"
    echo "   - Linux: sudo systemctl start mysql"
    echo "   - Windows: net start mysql"
    exit 1
fi

echo "✅ MySQL 服务正在运行"

# 数据库配置
DB_NAME="fastapi_web"
DB_USER="root"
DB_PASSWORD="password"  # 请根据实际情况修改

echo "📋 数据库配置："
echo "   数据库名: $DB_NAME"
echo "   用户名: $DB_USER"
echo "   密码: $DB_PASSWORD"
echo ""

# 检查数据库是否存在
echo "🔍 检查数据库是否存在..."
DB_EXISTS=$(mysql -u$DB_USER -p$DB_PASSWORD -e "SHOW DATABASES LIKE '$DB_NAME';" 2>/dev/null | grep $DB_NAME)

if [ "$DB_EXISTS" ]; then
    echo "⚠️  数据库 '$DB_NAME' 已存在"
    echo "是否要删除并重新创建？(y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🗑️  删除现有数据库..."
        mysql -u$DB_USER -p$DB_PASSWORD -e "DROP DATABASE $DB_NAME;" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ 数据库删除成功"
        else
            echo "❌ 数据库删除失败，请检查权限"
            exit 1
        fi
    else
        echo "📦 使用现有数据库"
        exit 0
    fi
fi

# 创建数据库
echo "🏗️  创建数据库..."
mysql -u$DB_USER -p$DB_PASSWORD -e "CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 数据库 '$DB_NAME' 创建成功"
else
    echo "❌ 数据库创建失败，请检查："
    echo "   1. MySQL 用户名和密码是否正确"
    echo "   2. 用户是否有创建数据库的权限"
    echo "   3. MySQL 服务是否正常运行"
    exit 1
fi

# 验证数据库
echo "🔍 验证数据库..."
mysql -u$DB_USER -p$DB_PASSWORD -e "USE $DB_NAME; SELECT 'Database connection successful' as status;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 数据库连接测试成功"
else
    echo "❌ 数据库连接测试失败"
    exit 1
fi

echo ""
echo "🎉 MySQL 数据库初始化完成！"
echo ""
echo "📝 接下来的步骤："
echo "1. 确认 .env 文件中的数据库配置正确"
echo "2. 运行 FastAPI 应用: python -m app.main"
echo "3. 应用会自动创建数据表"
echo ""
echo "🔧 数据库连接字符串："
echo "DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost:3306/$DB_NAME"