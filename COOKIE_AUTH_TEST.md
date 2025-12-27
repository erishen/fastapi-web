# Cookie 认证测试指南

## 快速测试步骤

### 1. 启动后端服务

```bash
cd fastapi-web
# 确保环境变量配置正确
cat .env

# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
```

### 2. 启动前端服务

```bash
cd interview
pnpm dev --filter=@interview/admin
```

### 3. 访问页面

打开浏览器访问：http://localhost:3003/zh/api-integration

### 4. 测试登录

1. 在"认证管理"模块中输入：
   - 用户名：`admin`
   - 密码：查看 `.env` 文件中的 `ADMIN_PASSWORD_HASH` 对应的密码

2. 点击"登录"按钮

3. 预期结果：
   - ✅ 显示"登录成功"
   - ✅ 自动显示"已登录"状态
   - ✅ 自动加载商品列表和 Redis 数据

### 5. 验证 Cookie

**检查 Cookie 是否正确设置：**

1. 按 F12 打开浏览器开发者工具
2. 切换到 "Application" 标签
3. 左侧菜单选择 "Cookies" → "http://localhost:3003"
4. 查找名为 `access_token` 的 cookie

**预期 Cookie 属性：**
```
Name: access_token
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (JWT token)
Domain: localhost
Path: /
HttpOnly: ✓ (不能被 JavaScript 访问)
Secure: ✗ (开发环境，HTTP)
SameSite: Lax
```

### 6. 测试自动认证

**刷新页面：**
1. 按 F5 或点击刷新按钮
2. 预期结果：保持登录状态，无需重新登录

**商品操作：**
1. 创建新商品
2. 编辑商品
3. 删除商品
4. 预期结果：所有操作都自动认证成功

### 7. 测试登出

1. 点击"登出"按钮
2. 预期结果：
   - ✅ Cookie 被清除
   - ✅ 回到登录表单
   - ✅ 商品列表和 Redis 数据清空

**验证 Cookie 被清除：**
- 再次查看 Application → Cookies
- `access_token` cookie 应该不存在

### 8. 测试网络请求

**检查 API 请求：**

1. 打开 Network 标签
2. 过滤 "fastapi"
3. 查看任何 API 请求

**查看请求头：**
```
Request Headers:
  Content-Type: application/json
  Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**注意：**
- ❌ 不应该看到 `Authorization: Bearer ...` header（除非明确使用）
- ✅ 应该看到 `Cookie: access_token=...`

## API 测试（使用 curl）

### 1. 登录并保存 Cookie

```bash
# 登录请求
curl -X POST "http://localhost:8081/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=admin&password=your_password" \
  -c cookies.txt \
  -v

# 检查保存的 cookie
cat cookies.txt
```

### 2. 使用 Cookie 访问受保护接口

```bash
# 获取用户信息
curl -X GET "http://localhost:8081/auth/me" \
  -b cookies.txt \
  -v

# 预期响应：
# {"username":"admin","role":"admin"}
```

### 3. 获取商品列表

```bash
curl -X GET "http://localhost:8081/items/" \
  -b cookies.txt \
  -v
```

### 4. 登出

```bash
curl -X POST "http://localhost:8081/auth/logout" \
  -b cookies.txt \
  -c cookies.txt \
  -v

# 检查 cookie 被清除
cat cookies.txt
```

## 对比测试：Bearer Token vs Cookie

### Bearer Token 方式（兼容）

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST "http://localhost:8081/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=admin&password=your_password" \
  | jq -r '.access_token')

# 2. 使用 token 访问接口
curl -X GET "http://localhost:8081/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -v
```

### Cookie 方式（推荐）

```bash
# 1. 登录（自动保存 cookie）
curl -X POST "http://localhost:8081/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=admin&password=your_password" \
  -c cookies.txt

# 2. 使用 cookie 访问接口（自动发送）
curl -X GET "http://localhost:8081/auth/me" \
  -b cookies.txt
```

## 性能测试

### 测试自动 Cookie 发送

```javascript
// 在浏览器控制台执行
async function testCookieAuth() {
  const start = Date.now()
  
  for (let i = 0; i < 10; i++) {
    await fetch('/api/fastapi/auth/me', {
      credentials: 'include'
    })
  }
  
  const end = Date.now()
  console.log(`10次请求耗时: ${end - start}ms`)
}

testCookieAuth()
```

### 测试并发请求

```javascript
async function testConcurrentRequests() {
  const start = Date.now()
  
  const requests = Array(10).fill(null).map(() =>
    fetch('/api/fastapi/items/', {
      credentials: 'include'
    })
  )
  
  await Promise.all(requests)
  
  const end = Date.now()
  console.log(`10个并发请求耗时: ${end - start}ms`)
}

testConcurrentRequests()
```

## 常见问题排查

### 问题 1：Cookie 未设置

**检查步骤：**
1. 查看后端日志是否显示 "登录成功"
2. 检查响应头是否包含 `Set-Cookie`
3. 检查浏览器是否阻止了 cookie

**解决方案：**
- 检查 CORS 配置
- 确认 `credentials: 'include'` 已设置
- 检查浏览器的 Cookie 设置

### 问题 2：Cookie 未发送

**检查步骤：**
1. 打开 Network 标签
2. 查看请求头是否有 `Cookie:`
3. 检查 Cookie 是否过期

**解决方案：**
- 确认 `credentials: 'include'` 已设置
- 检查 Cookie 的 `Path` 和 `Domain`
- 重新登录

### 问题 3：跨域问题

**检查步骤：**
1. 查看浏览器控制台是否有 CORS 错误
2. 检查前端域名是否在 `allowed_origins` 中

**解决方案：**
```python
# 更新 allowed_origins
allowed_origins: List[str] = [
    "http://localhost:3003",
    "http://your-frontend-domain.com",
]
```

### 问题 4：生产环境 Cookie 不工作

**检查步骤：**
1. 确认使用 HTTPS
2. 检查 `APP_ENV=production`
3. 查看 Cookie 的 `Secure` 属性

**解决方案：**
```bash
# 设置环境变量
export APP_ENV=production

# 确保使用 HTTPS
# 生产环境的 secure=True 必须配合 HTTPS
```

## 安全测试

### 1. XSS 攻击测试

```javascript
// 尝试从 JavaScript 访问 cookie
console.log(document.cookie)
// 预期：httpOnly 的 access_token cookie 不会显示
```

### 2. CSRF 攻击测试

从其他站点发起请求（模拟）：
```html
<!-- 这应该被 SameSite: Lax 阻止 -->
<iframe src="http://localhost:8081/items/delete/1"></iframe>
```

### 3. Token 过期测试

1. 登录
2. 等待 30 分钟（或修改过期时间为 1 分钟测试）
3. 发起请求
4. 预期：返回 401 Unauthorized

## 性能基准测试

### Cookie 认证 vs Token 认证

```javascript
// 对比测试
async function benchmark() {
  const iterations = 100
  
  // Token 方式
  const tokenStart = Date.now()
  for (let i = 0; i < iterations; i++) {
    await fetch('/api/fastapi/auth/me', {
      headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
    })
  }
  const tokenEnd = Date.now()
  
  // Cookie 方式
  const cookieStart = Date.now()
  for (let i = 0; i < iterations; i++) {
    await fetch('/api/fastapi/auth/me', {
      credentials: 'include'
    })
  }
  const cookieEnd = Date.now()
  
  console.log(`Token 方式: ${tokenEnd - tokenStart}ms`)
  console.log(`Cookie 方式: ${cookieEnd - cookieStart}ms`)
}

benchmark()
```

## 监控和日志

### 查看后端日志

```bash
# 应该看到类似的日志
# 🔑 使用 Cookie token
# ✅ 用户 admin 认证成功
```

### 查看浏览器控制台

```bash
# 应该看到调试日志
# 🚀 GET /api/fastapi/auth/me
# 📡 Response: 200 OK
# ✅ Success: {"username":"admin","role":"admin"}
```

## 成功标准

- ✅ 登录后自动设置 Cookie
- ✅ 刷新页面保持登录状态
- ✅ API 请求自动发送 Cookie
- ✅ 登出后清除 Cookie
- ✅ Cookie 为 httpOnly，JavaScript 无法访问
- ✅ 跨域请求正常工作
- ✅ 生产环境 HTTPS 传输

## 下一步

1. **完整集成测试**
   - 测试所有受保护的接口
   - 测试各种场景（登录、登出、过期）

2. **性能优化**
   - 测试高并发场景
   - 优化 Redis 缓存

3. **安全审计**
   - 渗透测试
   - 代码审计

4. **生产部署**
   - 配置 HTTPS
   - 设置域名白名单
   - 监控和告警
