# Cookie 跨域问题修复说明

## 问题描述

用户报告：
- 登录成功后，刷新页面仍然报"加载 Redis 键失败: 无效的认证凭据"
- 其他 API 接口也返回 401 未认证错误

## 根本原因

### 问题分析

虽然后端正确设置了 httpOnly cookie，但是：

1. **前端使用 Next.js API 代理**
   ```
   前端 (localhost:3003)
     ↓
   Next.js API 路由 (/api/fastapi/*)
     ↓
   fetch 到 FastAPI (localhost:8081)
   ```

2. **Cookie 的域名不匹配**
   ```
   - Cookie 设置在: localhost:8081（后端域名）
   - Cookie 期望发送到: localhost:8081（后端域名）
   - 实际发送: localhost:3003（前端域名）
   ```

3. **fetch 调用缺少 credentials**
   ```typescript
   // packages/api-client/src/fastapi-client.ts
   const fetchOptions: RequestInit = {
     method,
     headers: requestHeaders,
     // ❌ 缺少 credentials: 'include'
   }
   ```

### 跨域 Cookie 机制

**SameSite Cookie 行为：**

1. **同站请求（Same Domain）**
   ```
   Cookie 自动发送 ✓
   ```

2. **跨站请求（Different Domain）**
   ```
   Cookie 默认不发送
   需要 credentials: 'include' ✓
   ```

3. **httpOnly Cookie**
   ```
   JavaScript 无法读取
   只能通过浏览器自动发送
   必须使用 credentials: 'include'
   ```

## 解决方案

### 修改前端的 fetch 调用

**修改前：**
```typescript
// packages/api-client/src/fastapi-client.ts
const fetchOptions: RequestInit = {
  method,
  headers: requestHeaders,
  // ❌ 缺少 credentials
}
```

**修改后：**
```typescript
// packages/api-client/src/fastapi-client.ts
const fetchOptions: RequestInit = {
  method,
  headers: requestHeaders,
  credentials: 'include',  // ✓ 发送 cookies
}
```

### 修改重定向处理

**修改前：**
```typescript
response = await fetch(redirectUrl, {
  method: 'GET',
  headers: originalHeaders,
  // ❌ 缺少 credentials
})
```

**修改后：**
```typescript
response = await fetch(redirectUrl, {
  method: 'GET',
  headers: originalHeaders,
  credentials: 'include',  // ✓ 发送 cookies
})
```

## 完整的 Cookie 流程

### 1. 登录流程

```
用户登录
  ↓
前端: fetch('/api/fastapi/auth/login', { credentials: 'include' })
  ↓
Next.js 代理: 转发到 FastAPI，保持 credentials
  ↓
FastAPI 后端: 验证用户，设置 cookie
  ↓
后端响应: Set-Cookie: access_token=...; HttpOnly; Path=/
  ↓
浏览器: 保存 cookie（与后端域名绑定）
```

### 2. 后续请求流程

```
用户操作（加载 Redis 键）
  ↓
前端: fetch('/api/fastapi/redis/keys', { credentials: 'include' })
  ↓
浏览器: 自动发送 access_token cookie（到 FastAPI 域名）
  ↓
Next.js 代理: 转发请求和 cookie
  ↓
FastAPI 后端: 从 request.cookies.get("access_token") 读取
  ↓
后端: 验证 JWT token
  ↓
后端: 返回数据
```

## Credentials 选项说明

### 1. omit（默认）

```typescript
fetch(url, {
  credentials: 'omit'  // ❌ 不发送 cookies
})
```

**行为：**
- 不发送任何 cookies
- 不发送 HTTP 认证
- 最安全的选项

### 2. same-origin

```typescript
fetch(url, {
  credentials: 'same-origin'  // ✅ 只发送同源 cookies
})
```

**行为：**
- 只发送同源（相同域名）的 cookies
- 跨域请求不发送 cookies

### 3. include（推荐）

```typescript
fetch(url, {
  credentials: 'include'  // ✅ 发送所有 cookies
})
```

**行为：**
- 发送同源和跨源的 cookies
- 发送 HTTP 认证
- 需要服务器 CORS 允许

## CORS 配置要求

使用 `credentials: 'include'` 时，后端必须正确配置 CORS：

```python
# app/middleware.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3003",  # 必须明确指定
        # 不能使用 "*"
    ],
    allow_credentials=True,  # 必须为 True
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**关键点：**
1. `allow_origins` 不能使用 `["*"]`
2. 必须使用 `allow_credentials=True`
3. 必须明确列出前端域名

## Cookie 配置要求

### 后端 Cookie 设置

```python
# app/routers/auth.py
@router.post("/login")
async def login(response: Response, ...):
    is_secure = settings.app_env == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,      # JavaScript 无法访问
        secure=is_secure,    # 生产环境 True
        samesite="lax",    # CSRF 保护
        max_age=1800,       # 30 分钟
        path="/",
    )
```

### Cookie 属性说明

| 属性 | 值 | 作用 |
|------|-----|------|
| HttpOnly | True | 防止 XSS 攻击 |
| Secure | True (生产） | 只通过 HTTPS 传输 |
| SameSite | Lax | CSRF 保护，允许跨站 GET |
| Path | / | 对所有路径有效 |
| Max-Age | 1800 | 30 分钟过期 |

## 测试验证

### 1. 检查 Cookie 设置

**浏览器开发者工具：**
```
Application → Cookies → localhost:8081
```

**预期 Cookie：**
```
Name: access_token
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Domain: localhost
Path: /
HttpOnly: ✓
Secure: ✗ (开发）
SameSite: Lax
```

### 2. 检查网络请求

**Network 标签：**
```
Request URL: http://localhost:3003/api/fastapi/redis/keys
Request Method: GET
Request Headers:
  Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**注意：** 应该看到 `Cookie: access_token=...`

### 3. 测试功能

**登录测试：**
1. 输入用户名密码
2. 点击"登录"
3. 预期：登录成功，Cookie 被设置

**刷新测试：**
1. 按 F5 刷新页面
2. 预期：保持登录状态

**Redis 测试：**
1. 点击"刷新 Redis 键"
2. 预期：正常加载，不报 401

**商品测试：**
1. 点击"刷新商品列表"
2. 预期：正常加载，不报 401

## 重新构建

修改 `@interview/api-client` 包后，需要重新构建：

```bash
# 在项目根目录
cd interview

# 重新构建所有包
pnpm build

# 或者只构建 api-client 包
pnpm build --filter=@interview/api-client
```

然后重启开发服务器：

```bash
# 重启 admin 应用
pnpm dev --filter=@interview/admin
```

## 故障排查

### 问题 1：仍然返回 401

**检查：**
1. 包是否重新构建
   ```bash
   pnpm build --filter=@interview/api-client
   ```

2. 开发服务器是否重启
   - 停止并重新启动 admin 应用

3. Cookie 是否存在
   - Application → Cookies

4. 网络请求是否有 Cookie
   - Network 标签查看请求头

### 问题 2：Cookie 未设置

**检查：**
1. 后端是否正确设置 cookie
   ```python
   response.set_cookie(
       key="access_token",
       value=access_token,
       httponly=True,
       # ...
   )
   ```

2. CORS 配置是否正确
   - `allow_credentials=True`
   - `allow_origins` 包含前端域名

3. 响应头是否包含 Set-Cookie
   - Network 标签查看登录响应

### 问题 3：跨域错误

**错误信息：**
```
Access to fetch at 'http://localhost:8081/...' from origin 'http://localhost:3003' 
has been blocked by CORS policy
```

**解决方案：**
```python
# 确保 allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003"],  # 明确指定
    allow_credentials=True,  # 关键
)
```

## 总结

通过这次修复：

1. ✅ **添加了 credentials: 'include'**
   - 确保浏览器自动发送 cookies
   - 包括 httpOnly cookies

2. ✅ **修复了跨域 cookie 发送**
   - 即使域名不同，也发送 cookies
   - 配合 CORS 配置工作

3. ✅ **完整了 Cookie 认证流程**
   - 登录 → 设置 cookie
   - 请求 → 自动发送 cookie
   - 验证 → 后端读取并验证

4. ✅ **保持安全性**
   - httpOnly 防止 XSS
   - SameSite 防止 CSRF
   - Secure 防止中间人攻击

## 相关文档

- [Cookie 认证使用指南](./COOKIE_AUTH_GUIDE.md)
- [Cookie 认证测试指南](./COOKIE_AUTH_TEST.md)
- [Cookie 认证刷新测试](./COOKIE_REFRESH_TEST.md)
- [Cookie 认证修改总结](./COOKIE_AUTH_CHANGES.md)
- [Cookie 认证修复说明](./COOKIE_AUTH_FIX.md)

## 下一步

1. **重新构建包**
   ```bash
   pnpm build --filter=@interview/api-client
   ```

2. **重启开发服务器**
   ```bash
   pnpm dev --filter=@interview/admin
   ```

3. **测试验证**
   - 登录功能
   - 刷新页面
   - Redis 操作
   - 商品操作

4. **监控日志**
   - 查看浏览器控制台
   - 查看后端日志
   - 查看网络请求
