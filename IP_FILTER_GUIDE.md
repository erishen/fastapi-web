# IP 黑名单/白名单使用指南

## 快速开始

### 1. 编辑配置文件

```bash
vim .env.aliyun
```

### 2. 配置 IP 过滤

#### 黑名单（阻止特定 IP）

```bash
# 阻止单个 IP
IP_BLACKLIST=45.139.104.171

# 阻止多个 IP（逗号分隔）
IP_BLACKLIST=45.139.104.171, 203.0.113.0/24, 198.51.100.0/24

# 阻止 IP 段（CIDR 格式）
IP_BLACKLIST=203.0.113.0/24
```

#### 白名单（只允许特定 IP）

```bash
# 只允许特定 IP 访问
IP_WHITELIST=192.168.0.0/16, 172.16.0.0/12, 10.0.0.0/8

# 公司网络白名单示例
IP_WHITELIST=192.168.1.0/24

# 多个 IP 白名单
IP_WHITELIST=192.168.1.100, 192.168.1.101, 172.16.0.0/16
```

### 3. 重新加载配置

```bash
# 方式1：使用新命令（推荐）
make prod-reload

# 方式2：手动操作
cp .env.aliyun .env
docker-compose -f docker-compose.prod.yml restart

# 方式3：完整重启
make prod-up
```

### 4. 验证配置

```bash
# 查看容器环境变量
docker-compose -f docker-compose.prod.yml exec fastapi-web-app env | grep IP

# 查看日志确认
make prod-logs
```

---

## 常见使用场景

### 场景 1：阻止恶意 IP

```bash
# 查看日志，找到恶意 IP
make prod-logs

# 假设看到：
# 🚫 拒绝访问: IP=45.139.104.171, Path=/sendgrid.env

# 添加到黑名单
vim .env.aliyun
# 修改：IP_BLACKLIST=45.139.104.171

# 重新加载
make prod-reload
```

### 场景 2：阻止扫描 IP 段

```bash
# 某些 IP 段频繁扫描，可以整个网段阻止
vim .env.aliyun
# 修改：IP_BLACKLIST=45.139.104.0/24, 203.0.113.0/24

make prod-reload
```

### 场景 3：只允许公司网络访问

```bash
# 设置白名单模式
vim .env.aliyun
# 修改：IP_WHITELIST=192.168.0.0/16

# 重新加载
make prod-reload
```

### 场景 4：临时允许 IP

```bash
# 临时允许某个 IP 访问（用于测试）
vim .env.aliyun
# 添加到白名单：IP_WHITELIST=1.2.3.4

make prod-reload

# 测试完成后移除
vim .env.aliyun
# 清空：IP_WHITELIST=

make prod-reload
```

---

## IP/CIDR 格式说明

### 单个 IP

```
192.168.1.1
203.0.113.100
45.139.104.171
```

### CIDR 网段（推荐）

```
192.168.0.0/16    # 192.168.0.0 - 192.168.255.255
172.16.0.0/12     # 172.16.0.0 - 172.31.255.255
10.0.0.0/8        # 10.0.0.0 - 10.255.255.255
203.0.113.0/24    # 203.0.113.0 - 203.0.113.255
```

### 常用 CIDR 网段

| 网段 | 范围 | 说明 |
|------|------|------|
| 10.0.0.0/8 | 10.0.0.0 - 10.255.255.255 | 私有网络 |
| 172.16.0.0/12 | 172.16.0.0 - 172.31.255.255 | 私有网络 |
| 192.168.0.0/16 | 192.168.0.0 - 192.168.255.255 | 私有网络 |
| 203.0.113.0/24 | 203.0.113.0 - 203.0.113.255 | 测试网段 |
| 198.51.100.0/24 | 198.51.100.0 - 198.51.100.255 | 测试网段 |

---

## 配置优先级

1. **白名单优先**：如果设置了 `IP_WHITELIST`，则只允许白名单中的 IP
2. **黑名单生效**：未设置白名单时，黑名单中的 IP 会被阻止
3. **自动黑名单**：异常行为会自动加入动态黑名单（重启后清空）

---

## 安全建议

### 1. 定期审查日志

```bash
# 查看最近的安全事件
make prod-logs | grep "🚫\|⚠️"
```

### 2. 使用白名单模式（高安全要求）

```bash
# 只允许公司网络
IP_WHITELIST=192.168.0.0/16
```

### 3. 分级防护

```bash
# 基础防护：黑名单已知恶意 IP
IP_BLACKLIST=45.139.104.171, 203.0.113.0/24

# 高级防护：启用白名单
IP_WHITELIST=192.168.0.0/16
```

### 4. 自动黑名单调优

```bash
# 根据业务调整阈值
AUTO_BLACKLIST_THRESHOLD=500  # 5分钟内超过500次请求
AUTO_BLACKLIST_WINDOW=300     # 时间窗口（秒）
```

---

## 故障排查

### 问题1：配置未生效

**症状：** 修改配置后仍然可以访问

**解决：**
```bash
# 确认配置已复制
cat .env | grep IP

# 重新加载配置
make prod-reload

# 验证容器环境变量
docker-compose -f docker-compose.prod.yml exec fastapi-web-app env | grep IP
```

### 问题2：无法访问服务

**症状：** 配置白名单后无法访问

**解决：**
```bash
# 检查白名单配置
cat .env | grep IP_WHITELIST

# 确认你的 IP 在白名单中
curl ifconfig.me

# 如果不在白名单，添加后重新加载
vim .env.aliyun
make prod-reload
```

### 问题3：误阻止了合法 IP

**症状：** 正常用户被阻止

**解决：**
```bash
# 查看被阻止的 IP
make prod-logs | grep "拒绝访问"

# 从黑名单移除该 IP
vim .env.aliyun
# 删除对应的 IP

make prod-reload
```

---

## 命令参考

```bash
# 查看当前配置
cat .env | grep IP_

# 修改配置
vim .env.aliyun

# 重新加载配置（推荐）
make prod-reload

# 查看日志
make prod-logs

# 查看容器环境变量
docker-compose -f docker-compose.prod.yml exec fastapi-web-app env | grep IP

# 查看容器 IP 统计
docker-compose -f docker-compose.prod.yml exec fastapi-web-app redis-cli -h 127.0.0.1 -p 6379 KEYS "ratelimit:*"
```

---

## 监控和告警

### 实时监控

```bash
# 实时查看安全事件
make prod-logs | grep --line-buffered "🚫\|⚠️"
```

### 定期检查

```bash
# 每天检查一次被阻止的 IP
make prod-logs | grep "拒绝访问" | awk '{print $NF}' | sort | uniq -c | sort -rn
```

### 自动化脚本（可选）

可以设置定时任务，定期：
1. 检查日志中的异常 IP
2. 自动更新黑名单
3. 发送告警通知

---

## 配置示例

### 基础配置（默认）

```bash
IP_BLACKLIST=
IP_WHITELIST=
```

### 严格配置（只允许公司网络）

```bash
IP_BLACKLIST=
IP_WHITELIST=192.168.0.0/16
```

### 防御配置（黑名单 + 自动检测）

```bash
IP_BLACKLIST=45.139.104.171, 203.0.113.0/24
IP_WHITELIST=
AUTO_BLACKLIST_THRESHOLD=500
```

### 高安全配置（白名单 + 黑名单）

```bash
IP_BLACKLIST=203.0.113.0/24
IP_WHITELIST=192.168.0.0/16
PATH_PROTECTION_STRICT=true
```
