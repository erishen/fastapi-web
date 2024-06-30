#!/bin/bash

# 检查 Python 是否已安装
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# 设置环境变量（如果有需要）
# export MY_ENV_VARIABLE=value
export APP_ENV=development

# 运行 Python 程序
echo "Running Python program..."
python -m app.main

# 检查程序是否成功运行
if [ $? -ne 0 ]; then
    echo "Failed to run Python program."
    exit 1
else
    echo "Python program ran successfully."
fi
