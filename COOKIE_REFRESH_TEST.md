# Cookie 认证刷新页面测试

## 问题背景

前端页面刷新后需要重新登录，这是因为：
1. 前端依赖 `token` 状态判断登录
2. 刷新后状态丢失
3. 虽然浏览器有 cookie，但前端不知道

## 解决方案

在页面加载时检查 cookie 认证状态：
```typescript
useEffect(() => {
  const checkAuthStatus = async () => {
    try {
      // 调用 /auth/me 接口检查 cookie
      const result = await apiCall<UserInfo>('/auth/me')
      if (result.success && result.data) {
        // 有 cookie，设置登录状态
        setUserInfo(result.data)
        setToken('authenticated')
      }
    } catch (error) {
      // 未登录
      console.log('未通过 cookie 认证')
    }
  }

  checkAuthStatus()
}, [])
```

## 测试步骤

### 1. 启动服务

```bash
# 终端 1：启动后端
cd fastapi-web
python -m uvicorn app.main:app --reload --port 8081

# 终端 2：启动前端
cd interview
pnpm dev --filter=@interview/admin
```

### 2. 登录测试

1. 访问：http://localhost:3003/zh/api-integration
2. 输入用户名和密码
3. 点击"登录"
4. **预期结果**：
   - ✅ 显示"登录成功"
   - ✅ 显示用户信息
   - ✅ 自动加载商品列表
   - ✅ 自动加载 Redis 数据

### 3. 验证 Cookie

**检查浏览器 Cookie：**
1. 按 F12 打开开发者工具
2. 切换到 "Application" 标签
3. 左侧选择 "Cookies" → "http://localhost:3003"
4. 查找 `access_token` cookie

**预期 Cookie：**
```
Name: access_token
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
HttpOnly: ✓
Secure: ✗ (开发环境）
SameSite: Lax
Path: /
```

### 4. 刷新页面测试

**关键测试：**
1. 按 F5 或点击浏览器刷新按钮
2. **预期结果**：
   - ✅ 保持登录状态（不显示登录表单）
   - ✅ 显示用户信息
   - ✅ 自动加载商品列表
   - ✅ 自动加载 Redis 数据

**如果需要重新登录，说明有问题。**

### 5. 检查网络请求

**打开 Network 标签：**
1. 过滤 "fastapi"
2. 查看刷新后的第一个请求

**预期请求：**
```
Request URL: http://localhost:3003/api/fastapi/auth/me
Request Method: GET
Request Headers:
  Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**预期响应：**
```
Status: 200 OK
Response: {"username":"admin","role":"admin"}
```

### 6. 登出测试

1. 点击"登出"按钮
2. **预期结果**：
   - ✅ Cookie 被清除
   - ✅ 回到登录表单
   - ✅ 用户信息、商品、Redis 数据都清空

**验证 Cookie 清除：**
- 再次查看 Application → Cookies
- `access_token` cookie 应该不存在

### 7. 重新登录测试

1. 重新输入用户名和密码
2. 点击"登录"
3. **预期结果**：
   - ✅ Cookie 重新设置
   - ✅ 保持登录状态
   - ✅ 数据自动加载

## 问题排查

### 问题 1：刷新后需要重新登录

**检查：**
1. 是否调用 `/auth/me` 接口
   - 打开 Network 标签，查看刷新后的请求
   - 应该有对 `/api/fastapi/auth/me` 的调用

2. Cookie 是否存在
   - Application → Cookies
   - 检查 `access_token` 是否存在且未过期

3. 后端是否正确返回用户信息
   - Network 标签查看 `/api/fastapi/auth/me` 响应
   - 应该返回 200 和用户信息

**解决方案：**
```typescript
// 确保页面加载时检查认证
useEffect(() => {
  const checkAuthStatus = async () => {
    const result = await apiCall<UserInfo>('/auth/me')
    if (result.success && result.data) {
      setUserInfo(result.data)
      setToken('authenticated')
    }
  }
  checkAuthStatus()
}, [])
```

### 问题 2：Cookie 未设置

**检查：**
1. 查看后端日志
   - 应该看到 "登录成功"
   - 应该看到调用 `response.set_cookie()`

2. 查看响应头
   - Network 标签 → 登录请求 → Response Headers
   - 应该包含 `Set-Cookie: access_token=...`

3. 检查 CORS 配置
   - `allow_credentials=True`
   - 前端域名在 `allowed_origins` 中

**解决方案：**
```python
# app/middleware.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,  # 必须为 True
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### 问题 3：/auth/me 返回 401

**检查：**
1. Cookie 是否正确发送
   - Network 标签 → Request Headers
   - 应该包含 `Cookie: access_token=...`

2. Cookie 是否过期
   - Application → Cookies
   - 检查过期时间（默认 30 分钟）

3. 后端日志
   - 是否显示 JWT decode error
   - 是否显示 token 验证失败

**解决方案：**
- 重新登录获取新的 cookie
- 检查 token 过期时间配置

### 问题 4：登出后 Cookie 仍然存在

**检查：**
1. 是否调用 `/auth/logout` 接口
   - Network 标签查看请求

2. 响应头是否包含清除 cookie
   - Response Headers 应该包含 `Set-Cookie: access_token=; Max-Age=0`

**解决方案：**
```typescript
// 确保调用登出接口
const handleLogout = async () => {
  await apiCall('/auth/logout', { method: 'POST' })
  // 清除本地状态
  setToken('')
  setUserInfo(null)
}
```

## 调试技巧

### 1. 添加调试日志

```typescript
useEffect(() => {
  const checkAuthStatus = async () => {
    console.log('🔍 检查认证状态...')

    const result = await apiCall<UserInfo>('/auth/me')
    console.log('📡 认证结果:', result)

    if (result.success && result.data) {
      console.log('✅ 已登录:', result.data)
      setUserInfo(result.data)
      setToken('authenticated')
    } else {
      console.log('❌ 未登录')
    }
  }

  checkAuthStatus()
}, [])
```

### 2. 监控 cookie 变化

```javascript
// 在浏览器控制台执行
setInterval(() => {
  const cookies = document.cookie.split(';').map(c => c.trim())
  const accessToken = cookies.find(c => c.startsWith('access_token='))
  console.log('🍪 当前 cookie 状态:', accessToken ? '存在' : '不存在')
}, 2000)
```

### 3. 查看后端日志

```bash
# 后端应该输出类似日志
# 🔑 使用 Cookie token
# ✅ 用户 admin 认证成功
```

### 4. 使用浏览器开发者工具

**Application 标签：**
- Cookies：查看所有 cookie
- Local Storage：确认没有存储 token
- Session Storage：确认没有存储 token

**Network 标签：**
- 查看 API 请求和响应
- 检查请求头和响应头
- 查看 cookie 是否自动发送

## 成功标准

- ✅ 登录后自动设置 cookie
- ✅ 刷新页面保持登录状态（关键！）
- ✅ API 请求自动发送 cookie
- ✅ 登出后清除 cookie
- ✅ 重新登录正常工作
- ✅ Cookie 为 httpOnly（JavaScript 无法访问）

## 预期流程

```
1. 页面加载
   ↓
2. 调用 /auth/me 检查 cookie
   ↓
3a. 有 cookie → 显示登录状态
   ↓
3b. 无 cookie → 显示登录表单
   ↓
4. 用户登录
   ↓
5. 后端设置 cookie
   ↓
6. 前端设置登录状态
   ↓
7. 用户刷新页面
   ↓
8. 重新调用 /auth/me 检查 cookie
   ↓
9. Cookie 仍在 → 保持登录状态 ✅
```

## 性能测试

### 测试多次刷新

```javascript
// 在浏览器控制台执行
async function testRefresh() {
  const iterations = 10

  for (let i = 0; i < iterations; i++) {
    console.log(`🔄 第 ${i + 1} 次刷新...`)
    location.reload()
    await new Promise(resolve => setTimeout(resolve, 2000))
  }
}

// testRefresh() // 警告：会刷新页面！
```

### 测试认证性能

```javascript
// 测试 /auth/me 响应时间
async function testAuthPerformance() {
  const start = Date.now()

  for (let i = 0; i < 5; i++) {
    await fetch('/api/fastapi/auth/me', {
      credentials: 'include'
    })
  }

  const end = Date.now()
  console.log(`5次认证请求耗时: ${end - start}ms`)
  console.log(`平均每次: ${(end - start) / 5}ms`)
}

testAuthPerformance()
```

## 常见错误

### Error 1: "未通过 cookie 认证"

**原因：**
- 页面加载时检查认证失败
- 可能是 cookie 不存在或过期

**解决：**
- 重新登录
- 检查 cookie 过期时间

### Error 2: "获取用户信息失败"

**原因：**
- `/auth/me` 接口调用失败
- 可能是网络问题或后端未启动

**解决：**
- 检查后端是否运行
- 检查网络连接

### Error 3: Cookie 无法在刷新后保持

**原因：**
- Cookie 的 `Path` 或 `Domain` 设置不正确
- 浏览器阻止了 cookie

**解决：**
```python
# 确保正确的 cookie 设置
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=is_secure,
    samesite="lax",
    max_age=1800,
    path="/",  # 确保路径正确
)
```

## 总结

通过以下步骤实现了刷新页面保持登录状态：

1. ✅ 页面加载时调用 `/auth/me` 检查 cookie
2. ✅ 如果有 cookie，设置登录状态
3. ✅ 登录后端设置 httpOnly cookie
4. ✅ 登出时清除 cookie
5. ✅ 前端依赖后端认证而非 localStorage

现在刷新页面会自动检查 cookie，无需重新登录！
