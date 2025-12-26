#!/bin/bash

# 停止开发环境

set -e

echo "🛑 停止 FastAPI 开发环境..."

docker-compose down

echo "✅ 开发环境已停止"
