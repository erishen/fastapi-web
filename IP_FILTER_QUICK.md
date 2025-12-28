# IP 黑名单/白名单 - 快速参考

## 🚀 快速操作

### 修改配置

```bash
vim .env.aliyun
```

### 黑名单示例

```bash
# 阻止单个 IP
IP_BLACKLIST=45.139.104.171

# 阻止 IP 段
IP_BLACKLIST=45.139.104.0/24, 203.0.113.0/24
```

### 白名单示例

```bash
# 只允许公司网络
IP_WHITELIST=192.168.0.0/16

# 多个 IP
IP_WHITELIST=192.168.1.100, 192.168.1.101
```

### 重新加载配置

```bash
# 推荐：使用新命令
make prod-reload

# 或手动操作
cp .env.aliyun .env
docker-compose -f docker-compose.prod.yml restart
```

---

## 📋 查看操作

### 查看当前配置

```bash
cat .env | grep IP_
```

### 查看安全日志

```bash
# 实时查看
make prod-logs | grep --line-buffered "🚫\|⚠️"

# 查看最近的事件
make prod-logs | grep "拒绝访问\|阻止敏感路径\|可疑访问"
```

### 查看容器环境变量

```bash
docker-compose -f docker-compose.prod.yml exec fastapi-web-app env | grep IP
```

---

## 🔧 常见场景

### 阻止恶意 IP

```bash
# 1. 查看日志找到 IP
make prod-logs

# 2. 添加到黑名单
vim .env.aliyun
# IP_BLACKLIST=45.139.104.171

# 3. 重新加载
make prod-reload
```

### 只允许公司网络

```bash
# 1. 设置白名单
vim .env.aliyun
# IP_WHITELIST=192.168.0.0/16

# 2. 重新加载
make prod-reload
```

### 查看本机 IP（用于白名单）

```bash
curl ifconfig.me
# 或
curl ipinfo.io/ip
```

---

## ⚠️ 注意事项

1. **白名单优先**：设置白名单后，只有白名单中的 IP 能访问
2. **自动黑名单**：异常行为会自动加入黑名单（重启后清空）
3. **CIDR 格式**：支持 IP 和 CIDR 网段格式
4. **生效时间**：使用 `make prod-reload` 立即生效

---

## 📖 详细文档

完整文档请查看：[IP_FILTER_GUIDE.md](./IP_FILTER_GUIDE.md)
