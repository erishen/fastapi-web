# 安全加固快速参考

## 已实施的安全措施

### 1. IP 过滤 (`app/ip_filter.py`)
✓ 黑名单功能
✓ 白名单功能
✓ 自动黑名单（基于异常行为检测）
✓ 访问统计和追踪

**配置：**
```bash
IP_BLACKLIST=192.168.1.0/24, 10.0.0.1
IP_WHITELIST=172.16.0.0/12
AUTO_BLACKLIST_THRESHOLD=500
```

---

### 2. 路径保护 (`app/path_protection.py`)
✓ 阻止访问敏感文件（.env, .git, .log, .sql, .key 等）
✓ 检测并记录可疑爬虫访问
✓ 严格模式（可选）

**配置：**
```bash
PATH_PROTECTION_STRICT=false  # 设置为 true 启用严格模式
```

**受保护的文件类型：**
- 环境变量文件：.env, sendgrid.env
- 版本控制：.git, .hg, .svn
- 配置文件：.idea, .vscode, .config
- 备份文件：.bak, .backup, .old, .tmp
- 日志文件：.log
- 数据库文件：.sql, .db, .sqlite
- 密钥文件：.key, .pem, .crt, .p12
- 其他：.DS_Store, thumbs.db

---

### 3. robots.txt (`app/routers/system.py`)
✓ 限制爬虫访问敏感路径
✓ 防止搜索引擎索引 API 文档

**访问：** `http://your-domain.com/robots.txt`

---

### 4. 速率限制 (`app/middleware.py`)
✓ 不同路径使用不同的速率限制
✓ Redis 支持（分布式友好）
✓ 详细的响应头

**限制策略：**
- 默认：100 次/60秒
- 登录：30 次/60秒
- 文档日志：20 次/60秒

**配置：**
```bash
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

---

### 5. 安全响应头 (`app/security_headers.py`)
✓ X-Frame-Options: DENY
✓ X-Content-Type-Options: nosniff
✓ X-XSS-Protection: 1; mode=block
✓ Referrer-Policy: strict-origin-when-cross-origin
✓ Permissions-Policy
✓ Content-Security-Policy（动态生成）
✓ HSTS（生产环境）

---

## 使用方法

### 快速开始

1. **重启应用**
```bash
docker-compose down
docker-compose up -d
```

2. **测试安全配置**
```bash
python test_security.py
```

### 添加 IP 黑名单

```bash
# 编辑 .env 文件
IP_BLACKLIST=45.139.104.171, 203.0.113.0/24

# 重启应用
docker-compose restart
```

### 启用白名单模式

```bash
# 编辑 .env 文件
IP_WHITELIST=192.168.0.0/16, 172.16.0.0/12

# 重启应用
docker-compose restart
```

### 启用严格模式

```bash
# 编辑 .env 文件
PATH_PROTECTION_STRICT=true

# 重启应用
docker-compose restart
```

---

## 日志监控

### 关键日志标识

- `🚫 阻止敏感路径访问` - 有人试图访问敏感文件
- `⚠️  可疑访问检测` - 爬虫探测行为
- `⚠️  IP 自动加入黑名单` - 异常流量检测
- `🚫 拒绝访问` - IP 被黑名单/白名单阻止

### 查看日志

```bash
# Docker 环境
docker-compose logs -f fastapi-web-app

# 本地环境
tail -f logs/app.log
```

---

## 测试脚本

### 运行完整测试

```bash
python test_security.py
```

### 手动测试

```bash
# 测试敏感路径（应该返回 404）
curl http://localhost:8080/.env
curl http://localhost:8080/sendgrid.env

# 测试 robots.txt
curl http://localhost:8080/robots.txt

# 测试安全头
curl -I http://localhost:8080/
```

---

## 环境变量参考

### 完整安全配置

```bash
# ==================== 安全配置 ====================

# IP 黑名单/白名单
IP_BLACKLIST=192.168.1.0/24, 10.0.0.1
IP_WHITELIST=

# 自动黑名单配置
AUTO_BLACKLIST_THRESHOLD=500      # 5分钟内超过500次请求
AUTO_BLACKLIST_WINDOW=300         # 时间窗口（秒）
IP_CLEANUP_INTERVAL=600          # 清理间隔（秒）

# 路径保护
PATH_PROTECTION_STRICT=false     # 严格模式

# 速率限制
RATE_LIMIT_REQUESTS=100           # 默认限制
RATE_LIMIT_WINDOW=60              # 时间窗口（秒）
RATE_LIMIT_STRICT_REQUESTS=20     # 严格限制
RATE_LIMIT_STRICT_WINDOW=60
RATE_LIMIT_LOGIN_REQUESTS=30      # 登录限制
RATE_LIMIT_LOGIN_WINDOW=60

# JWT 密钥（必须设置）
SECRET_KEY=<使用 openssl rand -hex 32 生成>
NEXTAUTH_SECRET=<使用 openssl rand -hex 32 生成>

# 管理员密码哈希
ADMIN_PASSWORD_HASH=<使用 generate_password_hash.py 生成>

# 生产环境
APP_ENV=production
DEBUG=false
```

---

## 常见问题

### Q: 如何查看哪些 IP 被阻止了？

A: 查看日志中的 `🚫 拒绝访问` 或 `🚫 阻止敏感路径访问` 标识。

### Q: 速率限制太高，怎么调整？

A: 修改 `.env` 文件中的 `RATE_LIMIT_REQUESTS` 和 `RATE_LIMIT_WINDOW`。

### Q: 白名单和黑名单可以同时使用吗？

A: 可以。如果设置了白名单，则只允许白名单中的 IP 访问；黑名单会被忽略。

### Q: 严格模式会影响正常使用吗？

A: 严格模式会阻止所有可疑路径访问（如 `/admin`, `/login`），建议只在生产环境使用。

### Q: 如何恢复被自动黑名单的 IP？

A: 重启应用会清空动态黑名单。或者从 `.env` 中删除该 IP 后重启。

---

## 安全检查清单

### 生产环境部署前

- [ ] 设置 `APP_ENV=production`
- [ ] 设置 `DEBUG=false`
- [ ] 生成并设置强密钥（`SECRET_KEY`, `NEXTAUTH_SECRET`）
- [ ] 配置 `IP_BLACKLIST` 或 `IP_WHITELIST`
- [ ] 启用 `PATH_PROTECTION_STRICT=true`
- [ ] 根据流量调整 `RATE_LIMIT_REQUESTS`
- [ ] 测试安全配置（运行 `test_security.py`）
- [ ] 确认 `.env` 文件不在代码仓库中
- [ ] 检查日志监控配置

---

## 文件清单

新增文件：
- `app/ip_filter.py` - IP 过滤中间件
- `app/path_protection.py` - 路径保护中间件
- `test_security.py` - 安全测试脚本
- `SECURITY_SETUP.md` - 详细安全指南
- `SECURITY_QUICK_REFERENCE.md` - 本文件

修改文件：
- `app/factory.py` - 集成新的安全中间件
- `app/routers/system.py` - 添加 robots.txt 路由
- `.env.example` - 添加新的安全配置项

---

## 下一步

1. 阅读 `SECURITY_SETUP.md` 了解详细配置
2. 运行 `test_security.py` 测试当前配置
3. 根据需求调整 `.env` 文件
4. 配置日志监控和告警
5. 定期检查安全日志，更新 IP 黑名单

---

## 支持

如有问题，请查看：
- `SECURITY_SETUP.md` - 详细文档
- `test_security.py` - 测试示例
- 应用日志 - 实时监控
