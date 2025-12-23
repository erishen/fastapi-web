#!/bin/bash

# FastAPI Web 项目 Conda 环境设置脚本

echo "🚀 开始设置 FastAPI Web 项目 Conda 环境..."

# 检查 conda 是否可用
if ! command -v conda &> /dev/null; then
    echo "❌ Conda 未找到，请先安装 Anaconda 或 Miniconda"
    exit 1
fi

# 显示当前 conda 信息
echo "📍 当前 Conda 版本: $(conda --version)"

# 环境名称
ENV_NAME="fastapi-web"

# 检查环境是否已存在
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "⚠️  环境 ${ENV_NAME} 已存在，是否删除并重新创建？(y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🗑️  删除现有环境..."
        conda env remove -n ${ENV_NAME}
    else
        echo "📦 使用现有环境..."
        conda activate ${ENV_NAME}
        echo "✅ 环境已激活！"
        exit 0
    fi
fi

# 创建新的 conda 环境
echo "� 创建 Conda 环境: ${ENV_NAME}..."
conda create -n ${ENV_NAME} python=3.11 -y

# 激活环境
echo "🔄 激活 Conda 环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${ENV_NAME}

# 安装核心依赖
echo "📥 安装核心依赖..."
conda install -c conda-forge fastapi=0.111.0 -y
conda install -c conda-forge uvicorn=0.30.1 -y
conda install -c conda-forge sqlalchemy=2.0.31 -y
conda install -c conda-forge pydantic=2.7.4 -y
conda install -c conda-forge python-dotenv=1.0.1 -y
conda install -c conda-forge python-multipart=0.0.9 -y

# 使用 pip 安装 conda-forge 中没有的包
echo "📥 使用 pip 安装额外依赖..."
pip install PyMySQL==1.1.1
pip install httpx==0.27.0
pip install orjson==3.10.5

echo "✅ Conda 环境设置完成！"
echo ""
echo "🎯 使用方法："
echo "1. 激活环境: conda activate ${ENV_NAME}"
echo "2. 运行项目: python -m app.main"
echo "3. 退出环境: conda deactivate"
echo ""
echo "🌐 项目将在 http://localhost:8080 启动"
echo ""
echo "📋 环境信息："
conda info --envs | grep ${ENV_NAME}

echo ""
echo "🔧 环境变量配置："
echo "如果需要创建环境变量文件，请运行以下命令："
echo ""
echo "# Docker 环境变量文件"
echo "cat > .env.docker << 'EOF'"
echo "# 应用配置"
echo "EXPOSE_PORT=8080"
echo "SECRET_KEY=your-secret-key-change-this-in-production"
echo ""
echo "# MySQL 数据库配置"
echo "MYSQL_PASSWORD=your-mysql-password"
echo "MYSQL_EXPOSE_PORT=3307"
echo ""
echo "# Redis 缓存配置"
echo "REDIS_PASSWORD=your-redis-password"
echo "REDIS_EXPOSE_PORT=6380"
echo "REDIS_URL=redis://:your-redis-password@redis:6379/0"
echo "EOF"
echo ""
echo "# 本地开发环境变量文件"
echo "cat > .env << 'EOF'"
echo "# 本地开发配置"
echo "DEBUG=true"
echo "MYSQL_HOST=localhost"
echo "REDIS_HOST=localhost"
echo "REDIS_PASSWORD=redispassword"
echo "REDIS_URL=redis://:redispassword@localhost:6380/0"
echo "EOF"