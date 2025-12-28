# FastAPI Web 应用安全加固指南

## 概述

本文档说明了 FastAPI Web 应用的安全加固措施，包括 IP 过滤、路径保护、速率限制等功能。

## 安全特性

### 1. IP 过滤（IP 黑名单/白名单）

#### 功能说明
- 支持黑名单：阻止特定 IP 或 IP 段访问
- 支持白名单：只允许特定 IP 或 IP 段访问
- 自动黑名单：基于异常行为自动将 IP 加入黑名单

#### 配置方法

在 `.env` 文件中添加：

```bash
# IP 黑名单（逗号分隔）
IP_BLACKLIST=192.168.1.0/24, 10.0.0.1, 203.0.113.0/24

# IP 白名单（逗号分隔，如果设置了，则只允许白名单中的 IP 访问）
IP_WHITELIST=192.168.0.0/16, 172.16.0.0/12
```

#### 自动黑名单配置

```bash
# 5分钟内超过500次请求自动加入黑名单
AUTO_BLACKLIST_THRESHOLD=500
AUTO_BLACKLIST_WINDOW=300
IP_CLEANUP_INTERVAL=600
```

#### 使用场景

**黑名单场景：**
- 已知恶意 IP
- 频繁扫描的 IP 段
- 来自特定国家的攻击 IP

**白名单场景：**
- 内网环境（只允许公司 IP 访问）
- 测试环境（只允许开发人员 IP）
- 高安全要求环境（只允许特定 IP 访问）

---

### 2. 路径保护

#### 功能说明
- 自动阻止访问敏感文件（.env, .git, .log, .sql, .key 等）
- 检测并记录可疑爬虫访问
- 支持严格模式（可选）

#### 受保护的路径模式

以下路径模式会被自动阻止：

```
.env, .git, .hg, .svn, .idea, .vscode
.dockerignore, .gitignore, .DS_Store, thumbs.db
.bak, .backup, .old, .tmp, .swp, .swo
.log, .sql, .key, .pem, .crt, .p12, .keystore, .jks
.wallet, .db, .sqlite, .mdb, .config, .secret
.password, .auth, .token, .credentials, sendgrid.env
```

#### 可疑路径检测

以下路径会被记录为可疑访问（默认允许）：

```
/admin, /login, /wp-, /phpmyadmin, /mysql, /backup
/setup, /install, /test, /debug
```

#### 严格模式配置

在 `.env` 文件中设置：

```bash
# 启用严格模式（阻止所有可疑路径）
PATH_PROTECTION_STRICT=true
```

#### 示例日志

```
⚠️  可疑访问检测: IP=45.139.104.171, Path=/admin, UA=Mozilla/5.0...
🚫 阻止敏感路径访问: IP=45.139.104.171, Path=/sendgrid.env, UA=Mozilla/5.0...
```

---

### 3. 速率限制

#### 功能说明
- 不同路径使用不同的速率限制策略
- 支持 Redis 存储（分布式环境友好）
- 返回详细的速率限制响应头

#### 速率限制策略

| 路径类型 | 限制 | 时间窗口 |
|---------|------|---------|
| 默认请求 | 100 次 | 60 秒 |
| 登录请求 | 30 次 | 60 秒 |
| 文档日志 POST | 20 次 | 60 秒 |

#### 配置方法

在 `.env` 文件中修改：

```bash
# 默认速率限制
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# 严格速率限制
RATE_LIMIT_STRICT_REQUESTS=20
RATE_LIMIT_STRICT_WINDOW=60

# 登录速率限制
RATE_LIMIT_LOGIN_REQUESTS=30
RATE_LIMIT_LOGIN_WINDOW=60
```

#### 响应头

成功时：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
```

超出限制时：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 60
Retry-After: 60
```

---

### 4. robots.txt

#### 功能说明
- 限制爬虫访问敏感路径
- 防止搜索引擎索引 API 文档和管理界面

#### robots.txt 内容

```
User-agent: *
Disallow: /api/
Disallow: /admin/
Disallow: /docs/
Disallow: /redoc/
Disallow: /openapi.json
Disallow: /auth/
Disallow: /redis/

Allow: /
```

#### 访问

访问 `http://your-domain.com/robots.txt` 查看。

---

### 5. 安全响应头

#### 已配置的安全头

| 头名称 | 值 | 说明 |
|-------|---|------|
| X-Frame-Options | DENY | 防止点击劫持 |
| X-Content-Type-Options | nosniff | 防止 MIME 类型嗅探 |
| X-XSS-Protection | 1; mode=block | XSS 防护 |
| Referrer-Policy | strict-origin-when-cross-origin | Referrer 策略 |
| Permissions-Policy | 多种限制 | 权限策略 |
| Content-Security-Policy | 动态生成 | 内容安全策略 |
| Strict-Transport-Security | 生产环境启用 | HSTS |

#### CSP 策略

开发环境：允许本地开发和 CDN
生产环境：更严格的限制

---

## 使用示例

### 示例 1：阻止特定 IP 段

```bash
# .env
IP_BLACKLIST=203.0.113.0/24, 198.51.100.0/24
```

### 示例 2：只允许公司网络访问

```bash
# .env
IP_WHITELIST=192.168.0.0/16, 172.16.0.0/12, 10.0.0.0/8
```

### 示例 3：启用严格模式（生产环境）

```bash
# .env
PATH_PROTECTION_STRICT=true
```

### 示例 4：调整速率限制

```bash
# .env
# 生产环境：更严格的限制
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_WINDOW=60
RATE_LIMIT_STRICT_REQUESTS=10
```

---

## 安全最佳实践

### 1. 生产环境配置

```bash
# .env.production
APP_ENV=production
DEBUG=false
PATH_PROTECTION_STRICT=true
AUTO_BLACKLIST_THRESHOLD=300

# 使用强密钥
SECRET_KEY=<使用 openssl rand -hex 32 生成>
NEXTAUTH_SECRET=<使用 openssl rand -hex 32 生成>
```

### 2. 定期检查日志

监控日志中的以下信息：
- `🚫 阻止敏感路径访问` - 有人试图访问敏感文件
- `⚠️  可疑访问检测` - 爬虫探测行为
- `⚠️  IP 自动加入黑名单` - 异常流量

### 3. IP 黑名单管理

根据日志动态更新黑名单：

```bash
# 添加新的恶意 IP
IP_BLACKLIST=203.0.113.0/24, 198.51.100.0/24, <新IP段>
```

### 4. 定期审查

- 每月检查日志，更新 IP 黑名单
- 根据访问量调整速率限制
- 审查安全响应头配置

---

## 故障排查

### 问题：所有请求都被阻止

**原因：** 可能设置了白名单，但你的 IP 不在白名单中

**解决：** 检查 `IP_WHITELIST` 配置

### 问题：频繁收到 429 错误

**原因：** 速率限制触发

**解决：** 调整 `RATE_LIMIT_REQUESTS` 或增加时间窗口

### 问题：robots.txt 返回 404

**原因：** 路由未注册

**解决：** 确保 `system.router` 已在 `factory.py` 中注册

---

## 监控和告警

建议配置以下监控项：

1. **IP 黑名单触发次数**
2. **敏感路径访问尝试次数**
3. **速率限制触发次数**
4. **可疑路径访问次数**

可以集成以下工具：
- Sentry（错误追踪）
- Datadog（监控）
- Prometheus（指标收集）
- ELK Stack（日志分析）

---

## 安全检查清单

- [ ] 生产环境已配置 `APP_ENV=production`
- [ ] 已设置强密钥（`SECRET_KEY`, `NEXTAUTH_SECRET`）
- [ ] 已配置 `IP_BLACKLIST` 或 `IP_WHITELIST`（根据需求）
- [ ] 已启用 `PATH_PROTECTION_STRICT=true`（生产环境）
- [ ] 已根据流量调整速率限制
- [ ] 已配置日志监控
- [ ] 已测试 robots.txt 访问
- [ ] 已测试安全响应头
- [ ] 已检查敏感文件是否在代码仓库中
- [ ] 已配置环境变量保护（不要提交 .env 到 git）

---

## 进一步阅读

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI 安全最佳实践](https://fastapi.tiangolo.com/tutorial/security/)
- [CSP 快速入门](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [速率限制最佳实践](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
