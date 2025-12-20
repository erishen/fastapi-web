#!/bin/bash

# 检查 conda 是否已安装
if ! command -v conda &> /dev/null; then
    echo "Conda is not installed. Please install Anaconda or Miniconda and try again."
    exit 1
fi

# 激活 conda 环境
source $(conda info --base)/etc/profile.d/conda.sh
conda activate fastapi-web

# 检查环境是否存在
if [ $? -ne 0 ]; then
    echo "Conda environment 'fastapi-web' not found. Please run ./scripts/setup_env.sh first."
    exit 1
fi

# 设置环境变量（如果有需要）
export APP_ENV=development

# 运行 Python 程序
echo "Running FastAPI application in conda environment..."
python -m app.main

# 检查程序是否成功运行
if [ $? -ne 0 ]; then
    echo "Failed to run FastAPI application."
    exit 1
else
    echo "FastAPI application ran successfully."
fi
