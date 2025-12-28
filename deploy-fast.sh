#!/bin/bash

# 快速部署脚本 - 使用国内镜像源加速构建

echo "=========================================="
echo "FastAPI Web 应用快速部署"
echo "=========================================="
echo ""

# 备份原 Dockerfile
if [ -f Dockerfile ]; then
    echo "📦 备份原 Dockerfile..."
    cp Dockerfile Dockerfile.backup
fi

# 使用优化版 Dockerfile
if [ -f Dockerfile.optimized ]; then
    echo "⚡ 使用优化版 Dockerfile（国内镜像加速）..."
    cp Dockerfile.optimized Dockerfile
else
    echo "⚠️  Dockerfile.optimized 不存在，使用原版 Dockerfile"
fi

# 构建镜像
echo ""
echo "🔨 开始构建生产环境镜像..."
echo "=========================================="
make prod-build

# 恢复原 Dockerfile
if [ -f Dockerfile.backup ]; then
    echo ""
    echo "📦 恢复原 Dockerfile..."
    mv Dockerfile.backup Dockerfile
fi

echo ""
echo "=========================================="
echo "✅ 构建完成！"
echo "=========================================="
echo ""
echo "📋 下一步操作："
echo "  make prod-up      # 启动生产环境"
echo "  make prod-restart # 重启生产环境"
echo "  make prod-logs    # 查看生产环境日志"
echo ""
