#!/usr/bin/env bash

# 前端问题诊断脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "========================================="
echo "FastAPI 前端问题诊断"
echo "========================================="
echo ""

# 1. 检查 Redis 中的速率限制记录
echo "1️⃣  检查速率限制记录（Redis）..."

REDIS_PASSWORD=$(grep '^REDIS_PASSWORD=' .env 2>/dev/null | cut -d= -f2- || echo 'redis_password')
REDIS_PORT=$(grep '^REDIS_PORT=' .env 2>/dev/null | cut -d= -f2- || echo '6379')

if command -v redis-cli >/dev/null 2>&1; then
    echo "检查 Redis 中的速率限制记录..."
    
    RATE_LIMIT_KEYS=$(redis-cli -p $REDIS_PORT -n 0 -a $REDIS_PASSWORD --scan "ratelimit:*" 2>/dev/null | wc -l || echo "0")
    echo "  速率限制记录数: $RATE_LIMIT_KEYS"
    
    if [ $RATE_LIMIT_KEYS -gt 0 ]; then
        echo ""
        echo "  最近的速率限制记录:"
        redis-cli -p $REDIS_PORT -n 0 -a $REDIS_PASSWORD --scan "ratelimit:*" 2>/dev/null | head -5 | while read key; do
            count=$(redis-cli -p $REDIS_PORT -n 0 -a $REDIS_PASSWORD GET "$key" 2>/dev/null || echo "N/A")
            echo "    $key: $count 请求"
        done
    fi
else
    echo "  Redis 客户端未安装"
fi
echo ""

# 2. 检查容器日志
echo "2️⃣  检查容器日志中的错误..."
echo ""

if docker ps | grep -q fastapi-web-app; then
    echo "最近的 API 错误（过去 50 行）："
    docker logs fastapi-web-app --tail 50 2>&1 | grep -E "(401|403|429|500)" | tail -10 || echo "  无错误"
else
    echo "  容器未运行"
fi
echo ""

# 3. 测试 API 端点
echo "3️⃣  测试 API 端点..."
echo ""

PORT=$(grep '^PORT=' .env 2>/dev/null | cut -d= -f2- || echo '8086')
FASTAPI_URL="http://localhost:${PORT}"

# 测试健康检查
echo "  健康检查: "
if curl -s -f "${FASTAPI_URL}/health" >/dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 失败"
fi

# 测试登录端点（需要密码，跳过测试）
echo "  登录端点: /auth/login (跳过测试，需要密码)"

# 测试 token-from-nextauth 端点
echo "  Token 转换: /auth/token-from-nextauth (需要 NextAuth token)"

echo ""
# 4. 检查配置一致性
echo "4️⃣  检查配置一致性..."
echo ""

# 检查 SECRET_KEY
SECRET_KEY=$(grep '^SECRET_KEY=' .env 2>/dev/null | cut -d= -f2-)
if [ -n "$SECRET_KEY" ]; then
    KEY_LENGTH=${#SECRET_KEY}
    if [ $KEY_LENGTH -ge 32 ]; then
        echo "  ✅ SECRET_KEY: ${KEY_LENGTH} 字符（满足要求 ≥32）"
    else
        echo "  ⚠️  SECRET_KEY: ${KEY_LENGTH} 字符（太短，要求 ≥32）"
    fi
else
    echo "  ❌ SECRET_KEY 未配置"
fi

# 检查 NEXTAUTH_SECRET
NEXTAUTH_SECRET=$(grep '^NEXTAUTH_SECRET=' .env 2>/dev/null | cut -d= -f2-)
if [ -n "$NEXTAUTH_SECRET" ]; then
    echo "  ✅ NEXTAUTH_SECRET: 已配置"
else
    echo "  ⚠️  NEXTAUTH_SECRET 未配置"
fi

# 检查 DOC_LOG_API_KEY
DOC_LOG_API_KEY=$(grep '^DOC_LOG_API_KEY=' .env 2>/dev/null | cut -d= -f2-)
if [ -n "$DOC_LOG_API_KEY" ]; then
    echo "  ✅ DOC_LOG_API_KEY: 已配置"
else
    echo "  ⚠️  DOC_LOG_API_KEY 未配置（生产环境需要）"
fi

echo ""
# 5. 建议和修复步骤
echo "5️⃣  建议和修复步骤"
echo ""

echo "问题 1: 429 Too Many Requests"
echo "  原因: 15 分钟内登录尝试超过 5 次"
echo "  解决方案:"
echo "    1. 前端添加 Token 缓存（优先）"
echo "    2. 添加请求防抖（5 秒冷却）"
echo "    3. 检查密码是否正确"
echo ""

echo "问题 2: 403 Forbidden"
echo "  原因: 缺少或无效的 Authorization 头"
echo "  解决方案:"
echo "    1. 前端在请求时携带 Bearer Token"
echo "    2. 确保使用正确的 Token"
echo "    3. 检查用户角色是否为 admin"
echo ""

echo "6️⃣  前端代码修改建议"
echo ""
echo "需要修改的文件:"
echo "  - interview/apps/admin/src/lib/fastapi-client.ts (新建）"
echo "  - interview/apps/admin/src/components/DocLogs.tsx (修改）"
echo ""
echo "详细步骤请参考: FRONTEND_ISSUES_FIX.md"
echo ""

echo "========================================="
echo "诊断完成"
echo "========================================="
