# FastAPI 前端集成指南

## 错误诊断

### 问题 1: 403 Forbidden 错误

**症状：**
```
GET /api/fastapi/api/docs/logs 403
GET /api/fastapi/api/docs/stats 403
```

**原因：**
- 缺少或无效的 `Authorization` 请求头
- Token 已过期
- 用户角色不是 admin

**解决方案：**

前端需要按以下流程操作：

```typescript
// 1. NextAuth 登录后，获取 FastAPI Token
const nextAuthResponse = await fetch('/api/auth/passport/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token: nextAuthSession.token })
});

const { access_token } = await nextAuthResponse.json();

// 2. 存储 FastAPI Token（推荐使用 localStorage）
localStorage.setItem('fastapi_token', access_token);

// 3. 后续请求携带 Bearer Token
const response = await fetch('/api/fastapi/api/docs/logs', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

**完整示例：**

```typescript
// types/api.ts
export interface DocLog {
  id: number;
  action: string;
  doc_slug: string;
  user_id: string;
  user_email: string;
  user_name: string;
  auth_method: string;
  timestamp: string;
  details?: string;
}

// utils/fastapi.ts
export async function getFastAPIToken(): Promise<string> {
  const session = await getSession();
  if (!session) throw new Error('未登录');

  const response = await fetch('/api/auth/fastapi-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: session.token })
  });

  if (!response.ok) {
    throw new Error('获取 FastAPI Token 失败');
  }

  const data = await response.json();
  return data.access_token;
}

export function getAuthHeaders(token?: string): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

// api/docs.ts
export async function getDocLogs(accessToken?: string): Promise<DocLog[]> {
  const token = accessToken || localStorage.getItem('fastapi_token');

  if (!token) {
    throw new Error('缺少认证 Token');
  }

  const response = await fetch('/api/fastapi/api/docs/logs', {
    method: 'GET',
    headers: getAuthHeaders(token),
  });

  if (response.status === 403) {
    throw new Error('权限不足或 Token 无效，请重新登录');
  }

  if (!response.ok) {
    throw new Error('获取日志失败');
  }

  const data = await response.json();
  return data.logs;
}

// pages/AdminDashboard.tsx
import { getDocLogs, getFastAPIToken } from '@/api/docs';

function AdminDashboard() {
  const [logs, setLogs] = useState<DocLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadLogs() {
      try {
        setLoading(true);
        setError(null);

        // 如果已有 token，直接使用；否则重新获取
        let token = localStorage.getItem('fastapi_token');

        if (!token) {
          token = await getFastAPIToken();
          localStorage.setItem('fastapi_token', token);
        }

        const data = await getDocLogs(token);
        setLogs(data);
      } catch (err: any) {
        console.error('加载日志失败:', err);

        if (err.message.includes('Token') || err.message.includes('认证')) {
          // Token 失效，清除并提示重新登录
          localStorage.removeItem('fastapi_token');
          setError('认证已过期，请重新登录');
        } else {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    }

    loadLogs();

    // 每 30 分钟刷新 Token（防止过期）
    const interval = setInterval(async () => {
      try {
        const newToken = await getFastAPIToken();
        localStorage.setItem('fastapi_token', newToken);
      } catch (err) {
        console.error('刷新 Token 失败:', err);
      }
    }, 30 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h1>文档操作日志</h1>
      {error && <div className="error">{error}</div>}
      {loading ? <p>加载中...</p> : (
        <table>
          <thead>
            <tr>
              <th>操作</th>
              <th>文档</th>
              <th>用户</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id}>
                <td>{log.action}</td>
                <td>{log.doc_slug}</td>
                <td>{log.user_name} ({log.user_email})</td>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

---

### 问题 2: 429 Too Many Requests 错误

**症状：**
```
POST /api/admin/fastapi-login 429
```

**原因：**
- 15 分钟内超过 5 次登录尝试
- Token 刷新过于频繁

**解决方案：**

1. **优化 Token 刷新策略**

```typescript
// ❌ 错误：每次页面加载都刷新 Token
useEffect(() => {
  async function refreshToken() {
    const token = await getFastAPIToken();
    localStorage.setItem('fastapi_token', token);
  }
  refreshToken(); // 每次都刷新
}, []);

// ✅ 正确：只在 Token 不存在时刷新
useEffect(() => {
  async function refreshToken() {
    const existingToken = localStorage.getItem('fastapi_token');
    if (existingToken) {
      // 验证 Token 是否有效
      try {
        const response = await fetch('/api/auth/me', {
          headers: getAuthHeaders(existingToken)
        });
        if (response.ok) {
          return; // Token 有效，无需刷新
        }
      } catch (err) {
        // Token 无效，继续获取新的
      }
    }

    const newToken = await getFastAPIToken();
    localStorage.setItem('fastapi_token', newToken);
  }

  refreshToken();
}, []); // 只在组件挂载时执行一次
```

2. **添加重试逻辑**

```typescript
export async function getDocLogsWithRetry(): Promise<DocLog[]> {
  const MAX_RETRIES = 3;
  let retryCount = 0;

  while (retryCount < MAX_RETRIES) {
    try {
      return await getDocLogs();
    } catch (err: any) {
      retryCount++;

      if (err.message?.includes('429') && retryCount < MAX_RETRIES) {
        // 429 错误，等待后重试
        const waitTime = Math.pow(2, retryCount) * 1000; // 指数退避
        console.log(`429 错误，等待 ${waitTime}ms 后重试 (${retryCount}/${MAX_RETRIES})`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }

      throw err;
    }
  }

  throw new Error('重试次数已达上限');
}
```

3. **在用户层面限制**

```typescript
// 使用防抖，避免频繁点击
import { debounce } from 'lodash-es';

const debouncedLogin = debounce(async () => {
  await login();
}, 500);

// 调用
debouncedLogin();
```

---

### 问题 3: 401 Unauthorized 错误

**症状：**
```
GET /api/fastapi/api/docs/logs 401
```

**原因：**
- Token 格式错误
- Secret Key 配置不一致
- Token 确实过期

**解决方案：**

1. **验证 Secret Key 配置**

```bash
# .env.aliyun
SECRET_KEY=your-production-secret-key-here
NEXTAUTH_SECRET=nextauth-secret-key-here
NEXTAUTH_ADMIN_EMAILS=admin@example.com,ops@example.com
```

确保：
- `SECRET_KEY` 至少 32 字符
- `NEXTAUTH_SECRET` 与前端一致
- `NEXTAUTH_ADMIN_EMAILS` 包含当前登录用户的邮箱

2. **检查 Token 过期时间**

```typescript
// FastAPI Token 默认 60 分钟过期
// 建议在 Token 过期前 5 分钟刷新
export function shouldRefreshToken(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // 转为毫秒
    const now = Date.now();
    const FIVE_MINUTES = 5 * 60 * 1000;

    return exp - now < FIVE_MINUTES;
  } catch (err) {
    return true; // 解析失败，需要刷新
  }
}

useEffect(() => {
  if (shouldRefreshToken(currentToken)) {
    refreshToken();
  }
}, [currentToken]);
```

---

## API 接口列表

### 认证接口

#### 1. FastAPI 管理员登录
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin
password=your_password
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### 2. NextAuth Token 转换
```http
POST /api/auth/token-from-nextauth
Content-Type: application/json
Authorization: Bearer <nextauth_token>

{
  "token": "<nextauth_token>"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**注意：**
- 用户的 email 必须在 `NEXTAUTH_ADMIN_EMAILS` 列表中
- 如果不在列表中，返回 403 Forbidden

---

### 文档日志接口

#### 1. 记录文档操作
```http
POST /api/docs/log
Content-Type: application/json
X-API-Key: <your_api_key>

{
  "action": "view",
  "doc_slug": "getting-started",
  "user_id": "user123",
  "user_email": "user@example.com",
  "user_name": "User Name",
  "auth_method": "nextauth",
  "details": "optional details"
}
```

**X-API-Key 配置：**
```bash
# .env.aliyun
DOC_LOG_API_KEY=15ac5d71a278344bff026449ee12a1b70fe3c8b807cde285b88cbf292f1303cb
```

#### 2. 获取文档日志列表
```http
GET /api/fastapi/api/docs/logs
Authorization: Bearer <fastapi_token>
Content-Type: application/json

?limit=100&doc_slug=getting-started&action=view
```

**响应：**
```json
{
  "success": true,
  "logs": [
    {
      "id": 1,
      "action": "view",
      "doc_slug": "getting-started",
      "user_id": "user123",
      "user_email": "user@example.com",
      "user_name": "User Name",
      "auth_method": "nextauth",
      "timestamp": "2024-01-01T00:00:00Z",
      "details": "optional details"
    }
  ]
}
```

**需要认证：** Bearer Token（管理员权限）

#### 3. 获取文档统计
```http
GET /api/fastapi/api/docs/stats
Authorization: Bearer <fastapi_token>
```

**响应：**
```json
{
  "success": true,
  "stats": {
    "total": 150,
    "create": 45,
    "update": 80,
    "delete": 25,
    "by_user": {
      "user@example.com": 50,
      "admin@example.com": 100
    }
  }
}
```

**需要认证：** Bearer Token（管理员权限）

---

## 速率限制配置

| 接口 | 限制 | 时间窗口 |
|-------|-------|----------|
| `/api/auth/login` | 5 次 | 900 秒（15 分钟） |
| `/api/docs/log` | 20 次 | 60 秒（1 分钟） |
| 其他接口 | 100 次 | 60 秒（1 分钟） |

---

## 调试技巧

### 1. 查看响应头

```typescript
const response = await fetch('/api/fastapi/api/docs/logs', {
  headers: getAuthHeaders(token)
});

console.log('Rate Limit:', {
  limit: response.headers.get('X-RateLimit-Limit'),
  remaining: response.headers.get('X-RateLimit-Remaining'),
  reset: response.headers.get('X-RateLimit-Reset')
});
```

### 2. 捕获所有错误

```typescript
export async function apiRequest<T>(
  url: string,
  options: RequestInit
): Promise<T> {
  try {
    const response = await fetch(url, options);

    if (response.status === 401) {
      throw new AuthError('认证失败，请重新登录');
    }

    if (response.status === 403) {
      throw new PermissionError('权限不足');
    }

    if (response.status === 429) {
      const reset = response.headers.get('X-RateLimit-Reset');
      throw new RateLimitError('请求过于频繁', reset);
    }

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`);
    }

    return await response.json();
  } catch (err) {
    console.error('API 请求错误:', err);
    throw err;
  }
}
```

---

## 配置检查清单

### 后端配置（.env.aliyun）

```bash
# 必须配置
APP_ENV=production
SECRET_KEY=<至少32字符的字符串>
NEXTAUTH_SECRET=<与前端一致的密钥>
NEXTAUTH_ADMIN_EMAILS=<包含管理员邮箱>
DOC_LOG_API_KEY=<用于文档日志记录>

# 数据库配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=<your_mysql_password>
MYSQL_DATABASE=fastapi_web

# Redis 配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=<your_redis_password>
```

### 前端配置（NextAuth）

```typescript
// next.config.js
module.exports = {
  env: {
    NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET,
  },
  providers: [
    {
      id: 'fastapi',
      name: 'FastAPI',
      type: 'oauth',
      authorization: { ... },
      token: { ... },
    }
  ]
}
```

---

## 故障排查流程

1. **检查网络连接**
   ```bash
   curl https://api.erishen.cn/health
   ```

2. **验证 NextAuth Token**
   ```typescript
   const session = await getSession();
   console.log('NextAuth Token:', session?.token);
   ```

3. **获取 FastAPI Token**
   ```typescript
   const token = await getFastAPIToken();
   console.log('FastAPI Token:', token);
   ```

4. **测试 API 调用**
   ```bash
   # 使用 curl 测试
   curl -H "Authorization: Bearer <token>" \
     https://api.erishen.cn/api/fastapi/api/docs/logs
   ```

5. **查看服务日志**
   ```bash
   make prod-logs
   ```
