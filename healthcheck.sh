#!/bin/bash
set -e

# 使用环境变量或默认值
PORT=${PORT:-8080}

# 执行健康检查
curl -f http://localhost:${PORT}/health || exit 1
