#!/bin/bash
set -e

# 使用环境变量或默认值
PORT=${PORT:-8080}
HOST=${HOST:-0.0.0.0}

# 启动应用
exec uvicorn app.main:app --host "$HOST" --port "$PORT"
