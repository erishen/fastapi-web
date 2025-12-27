# HttpOnly Cookie 认证使用说明

## 概述

为了提高安全性，FastAPI 后端现在支持使用 httpOnly cookie 进行认证。这种方式比 localStorage 更安全，可以有效防止 XSS 攻击窃取 token。

## 安全优势

### HttpOnly Cookie vs localStorage

| 特性 | httpOnly Cookie | localStorage |
|------|----------------|---------------|
| XSS 防护 | ✅ JavaScript 无法访问 | ❌ 可被 JavaScript 读取 |
| CSRF 防护 | ✅ SameSite 保护 | ✅ 无此问题 |
| 自动发送 | ✅ 浏览器自动发送 | ❌ 需要手动添加到请求头 |
| 跨域支持 | ✅ 配合 CORS | ✅ 配合 CORS |
| 过期控制 | ✅ 服务器控制 | ❌ 客户端控制 |

## 实现细节

### 后端修改

#### 1. 认证路由 (`app/routers/auth.py`)

登录时设置 httpOnly cookie：

```python
@router.post("/login", response_model=Token)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    # ... 验证用户 ...

    # 设置 httpOnly cookie
    is_secure = settings.app_env == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,      # 防止 XSS
        secure=is_secure,    # 生产环境 HTTPS only
        samesite="lax",    # CSRF 保护
        max_age=1800,       # 30 分钟
        path="/"
    )

    # 为了兼容性，仍然返回 token
    return {"access_token": access_token, "token_type": "bearer"}
```

#### 2. 安全模块 (`app/security.py`)

支持两种认证方式：

```python
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    """支持 Bearer Token 和 httpOnly Cookie"""
    # 1. 尝试从 Authorization Header 获取
    if credentials and credentials.credentials:
        token = credentials.credentials
    # 2. 尝试从 cookie 获取
    else:
        token = request.cookies.get("access_token")

    # 验证 token
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    # ...
```

### 前端修改

#### 1. 移除 localStorage 管理

**之前（使用 localStorage）：**
```typescript
// 登录成功
setToken(result.access_token)
localStorage.setItem('fastapi_token', result.access_token)

// 页面加载
useEffect(() => {
  const savedToken = localStorage.getItem('fastapi_token')
  if (savedToken) {
    setToken(savedToken)
  }
}, [])
```

**现在（使用 cookie）：**
```typescript
// 登录成功 - 无需存储
// 后端已经设置了 cookie

// 页面加载 - 自动使用 cookie
// 无需手动加载
```

#### 2. API 调用配置

确保 `credentials: 'include'`：

```typescript
const response = await fetch(url, {
  headers: {
    'Content-Type': 'application/json',
    // 不需要手动添加 Authorization header
  },
  credentials: 'include', // 关键：让浏览器自动发送 cookie
  ...options,
})
```

## 使用方式

### 方式 1：httpOnly Cookie（推荐）

适用于：浏览器环境、标准 Web 应用

**前端：**
```typescript
// 登录
const result = await apiCall('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ username, password })
})
// Cookie 自动设置，无需手动管理

// 后续请求
const data = await apiCall('/items/list')
// 浏览器自动发送 cookie
```

**特点：**
- ✅ 自动认证，无需手动管理 token
- ✅ 安全性高，防止 XSS 攻击
- ✅ 用户体验好，刷新页面保持登录状态

### 方式 2：Bearer Token（兼容）

适用于：移动端、第三方应用、脚本

**前端：**
```typescript
// 登录
const result = await apiCall('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ username, password })
})
const token = result.access_token

// 后续请求
const data = await apiCall('/items/list', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

**特点：**
- ✅ 灵活性高，适用于多种客户端
- ✅ 不依赖浏览器的 cookie 机制
- ⚠️ 需要手动管理 token 存储

## 环境配置

### 开发环境（HTTP）

`.env` 文件：
```bash
APP_ENV=development
```

Cookie 设置：
```python
secure=False  # HTTP 协议允许发送
```

### 生产环境（HTTPS）

`.env` 文件：
```bash
APP_ENV=production
```

Cookie 设置：
```python
secure=True  # 仅 HTTPS 传输
```

## 登出功能

**前端：**
```typescript
const handleLogout = async () => {
  // 调用登出接口
  await apiCall('/auth/logout', { method: 'POST' })

  // 清除本地状态
  setToken('')
  setUserInfo(null)
  // Cookie 由后端清除
}
```

**后端：**
```python
@router.post("/logout")
async def logout(response: Response):
    """清除 httpOnly cookie"""
    is_secure = settings.app_env == "production"
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=is_secure,
        samesite="lax"
    )
    return {"message": "登出成功"}
```

## CORS 配置

确保 CORS 中间件支持 credentials：

```python
# app/middleware.py
def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,  # 关键：允许发送 cookie
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
        max_age=600,
    )
```

**前端域名必须明确指定：**
```python
allowed_origins: List[str] = [
    "http://localhost:3000",
    "http://localhost:3003",
    "https://yourdomain.com",  # 生产环境
]
```

## 安全注意事项

### 1. CSRF 保护

SameSite 策略：
- `lax`: 允许跨站 GET 请求（推荐）
- `strict`: 完全禁止跨站请求（更安全）
- `none`: 允许所有跨站请求（不推荐）

### 2. HTTPS

生产环境必须使用 HTTPS：
```python
secure=True  # 仅 HTTPS 传输 cookie
```

### 3. 密钥管理

确保使用强密钥：
```bash
# 生成强密钥
openssl rand -hex 32
```

### 4. Token 过期

设置合理的过期时间：
```bash
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 测试验证

### 1. 检查 Cookie

浏览器开发者工具 → Application → Cookies：
```
Name: access_token
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
HttpOnly: ✓
Secure: ✓ (生产环境) / ✗ (开发环境)
SameSite: Lax
Path: /
```

### 2. 检查请求

浏览器开发者工具 → Network → Request Headers：
```
Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. 登录流程

1. 用户输入用户名密码
2. 调用 `/auth/login` 接口
3. 后端验证用户，生成 JWT token
4. 后端设置 httpOnly cookie
5. 浏览器自动保存 cookie
6. 后续请求自动发送 cookie
7. 刷新页面保持登录状态

### 4. 登出流程

1. 调用 `/auth/logout` 接口
2. 后端清除 cookie
3. 前端清除本地状态
4. 用户需要重新登录

## 故障排查

### 问题 1：登录成功但认证失败

**检查：**
1. Cookie 是否正确设置（浏览器开发者工具）
2. CORS 配置是否正确
3. `credentials: 'include'` 是否设置

### 问题 2：跨域请求失败

**检查：**
1. 前端域名是否在 `allowed_origins` 中
2. `allow_credentials=True` 是否设置
3. SameSite 策略是否正确

### 问题 3：Cookie 不在 HTTPS 下工作

**检查：**
1. 生产环境是否使用 HTTPS
2. `secure=True` 是否在 HTTPS 环境
3. 使用 `APP_ENV=production` 确保正确配置

## 迁移指南

### 从 localStorage 迁移到 httpOnly Cookie

1. **移除 localStorage 代码**
   ```typescript
   // 删除
   localStorage.getItem('fastapi_token')
   localStorage.setItem('fastapi_token', token)
   localStorage.removeItem('fastapi_token')
   ```

2. **确保 API 调用配置**
   ```typescript
   fetch(url, {
     credentials: 'include', // 必须添加
     // ...
   })
   ```

3. **更新登录逻辑**
   ```typescript
   // 登录后不需要存储 token
   // 后端自动设置 cookie
   ```

4. **测试验证**
   - 登录功能
   - 刷新页面
   - API 调用
   - 登出功能

## 最佳实践

1. **生产环境使用 HTTPS**
2. **设置合理的过期时间**
3. **定期轮换密钥**
4. **监控异常登录**
5. **实现登出功能**
6. **提供记住我选项**
7. **双因素认证（可选）**

## 参考资料

- [OWASP Cookie Security](https://owasp.org/www-community/controls/SecureCookieAttribute)
- [MDN: HttpOnly](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
