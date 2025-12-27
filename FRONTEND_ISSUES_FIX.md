# FastAPI 前端集成问题修复方案

## 问题分析

从日志中看到两个主要问题：

### 1. 429 Too Many Requests
```
POST /api/admin/fastapi-login 429 in 67ms
POST /api/admin/fastapi-login 429 in 68ms
```

**原因：**
- 15 分钟内超过 5 次登录尝试
- 前端频繁请求 FastAPI token，可能没有缓存
- 用户刷新页面或导航时重复请求

### 2. 403 Forbidden
```
GET /api/fastapi/api/docs/logs? 403 in 36ms
GET /api/fastapi/api/docs/stats 403 in 30ms
```

**原因：**
- 缺少或无效的 `Authorization` 头
- Token 已过期
- 用户角色不是 admin

---

## 解决方案

### 方案 1：前端缓存 FastAPI Token（推荐）

**修改前端代码，添加 Token 缓存：**

```typescript
// lib/fastapi.ts

const FASTAPI_TOKEN_KEY = 'fastapi_admin_token';
const FASTAPI_TOKEN_EXPIRY_KEY = 'fastapi_admin_token_expiry';

export interface FastAPIToken {
  access_token: string;
  token_type: string;
  expires_at: number;
}

/**
 * 获取缓存的 Token（优先使用）
 */
export function getCachedFastAPIToken(): FastAPIToken | null {
  if (typeof window === 'undefined') return null;

  try {
    const cached = localStorage.getItem(FASTAPI_TOKEN_KEY);
    if (!cached) return null;

    const token = JSON.parse(cached) as FastAPIToken;

    // 检查是否过期（提前 5 分钟过期，防止边界情况）
    const FIVE_MINUTES = 5 * 60 * 1000;
    if (Date.now() > token.expires_at - FIVE_MINUTES) {
      console.log('[FastAPI] Token 已过期，需要刷新');
      localStorage.removeItem(FASTAPI_TOKEN_KEY);
      return null;
    }

    console.log('[FastAPI] 使用缓存的 Token');
    return token;
  } catch (err) {
    console.error('[FastAPI] 读取缓存失败:', err);
    return null;
  }
}

/**
 * 获取 FastAPI Token（带缓存）
 */
export async function getFastAPIToken(): Promise<FastAPIToken> {
  // 1. 尝试从缓存获取
  const cached = getCachedFastAPIToken();
  if (cached) {
    return cached;
  }

  console.log('[FastAPI] 缓存未命中，请求新 Token');

  // 2. 通过后端 API 获取
  const response = await fetch('/api/admin/fastapi-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || '获取 Token 失败');
  }

  const token = await response.json();
  
  // 3. 添加过期时间（60 分钟）
  const ONE_HOUR = 60 * 60 * 1000;
  const tokenWithExpiry: FastAPIToken = {
    ...token,
    expires_at: Date.now() + ONE_HOUR
  };

  // 4. 缓存 Token
  localStorage.setItem(FASTAPI_TOKEN_KEY, JSON.stringify(tokenWithExpiry));

  return tokenWithExpiry;
}

/**
 * 清除缓存的 Token
 */
export function clearFastAPIToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(FASTAPI_TOKEN_KEY);
  }
}
```

**使用示例：**

```typescript
// apps/admin/src/app/api/fastapi/api/docs/logs/route.ts
import { getFastAPIToken } from '@/lib/fastapi';

export async function GET(request: NextRequest) {
  try {
    const { access_token } = await getFastAPIToken();

    // 调用 FastAPI 接口
    const response = await fetch(`${FASTAPI_URL}/api/docs/logs`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      if (response.status === 403) {
        // Token 可能无效，清除缓存
        clearFastAPIToken();
        throw new Error('权限不足，正在重新认证...');
      }
      throw new Error(`API 请求失败: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('[API Error]:', error);
    return NextResponse.json(
      { error: error.message || '请求失败' },
      { status: 500 }
    );
  }
}
```

---

### 方案 2：添加登录防抖（避免频繁请求）

```typescript
// lib/fastapi.ts

let tokenPromise: Promise<FastAPIToken> | null = null;
let lastTokenRequest: number = 0;

export async function getFastAPITokenWithDebounce(): Promise<FastAPIToken> {
  const now = Date.now();
  const COOLDOWN_MS = 5000; // 5 秒内不重复请求

  // 如果有正在进行的请求，等待完成
  if (tokenPromise) {
    return tokenPromise;
  }

  // 如果 5 秒内已请求过，等待
  const timeSinceLastRequest = now - lastTokenRequest;
  if (timeSinceLastRequest < COOLDOWN_MS) {
    console.log(`[FastAPI] 请求冷却中 (${timeSinceLastRequest}ms)`);
    
    // 等待剩余冷却时间
    await new Promise(resolve => 
      setTimeout(resolve, COOLDOWN_MS - timeSinceLastRequest)
    );
    
    return getFastAPITokenWithDebounce();
  }

  // 开始新请求
  lastTokenRequest = now;
  tokenPromise = getFastAPIToken();

  try {
    const result = await tokenPromise;
    return result;
  } finally {
    tokenPromise = null;
  }
}
```

---

### 方案 3：后端调整速率限制（可选）

如果前端需要更灵活的请求频率，可以调整后端配置：

```python
# app/middleware.py

RATE_LIMITS: Dict[str, Dict[str, int]] = {
    "default": {
        "requests": 100,
        "window": 60
    },
    "strict": {
        "requests": 20,
        "window": 60
    },
    "login": {
        "requests": 10,  # 从 5 改为 10
        "window": 300  # 从 900 秒改为 300 秒（5 分钟）
    }
}
```

**注意：** 调整后端速率限制会增加安全风险，建议优先使用前端缓存方案。

---

## 完整集成示例

### 1. 创建 FastAPI 客户端封装

```typescript
// lib/fastapi-client.ts

interface FastAPIError {
  error: string;
  status?: number;
  details?: any;
}

export class FastAPIClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.FASTAPI_URL || 'http://localhost:8086';
  }

  async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await getFastAPIToken();

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token.access_token}`,
        ...options.headers
      }
    });

    // 处理 403/401 错误
    if (response.status === 401 || response.status === 403) {
      clearFastAPIToken();
      throw new Error('认证失败，请重新登录');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || '请求失败');
    }

    return response.json();
  }

  // 文档日志相关
  async getDocLogs(limit: number = 100, doc_slug?: string) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (doc_slug) params.set('doc_slug', doc_slug);
    
    return this.request<{ success: true; logs: any[] }>(
      `/api/docs/logs?${params}`
    );
  }

  async getDocStats() {
    return this.request<{ success: true; stats: any }>(
      `/api/docs/stats`
    );
  }

  async getMe() {
    return this.request<{ username: string; role: string }>(
      `/auth/me`
    );
  }
}

// 单例
export const fastapi = new FastAPIClient();
```

### 2. 在 React 组件中使用

```typescript
// apps/admin/src/components/DocLogs.tsx

'use client';

import { useState, useEffect } from 'react';
import { fastapi } from '@/lib/fastapi-client';

export default function DocLogs() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        // 并行加载日志和统计
        const [logsData, statsData] = await Promise.all([
          fastapi.getDocLogs(100),
          fastapi.getDocStats()
        ]);

        setLogs(logsData.logs);
        setStats(statsData.stats);
      } catch (err: any) {
        console.error('[DocLogs] 加载失败:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">文档操作日志</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8">加载中...</div>
      ) : (
        <>
          {/* 统计信息 */}
          {stats && (
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded">
                <div className="text-3xl font-bold">{stats.total}</div>
                <div className="text-gray-600">总操作</div>
              </div>
              <div className="bg-green-50 p-4 rounded">
                <div className="text-3xl font-bold">{stats.create}</div>
                <div className="text-gray-600">创建</div>
              </div>
              <div className="bg-yellow-50 p-4 rounded">
                <div className="text-3xl font-bold">{stats.update}</div>
                <div className="text-gray-600">更新</div>
              </div>
              <div className="bg-red-50 p-4 rounded">
                <div className="text-3xl font-bold">{stats.delete}</div>
                <div className="text-gray-600">删除</div>
              </div>
            </div>
          )}

          {/* 日志表格 */}
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">文档</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs rounded ${
                      log.action === 'view' ? 'bg-blue-100 text-blue-800' :
                      log.action === 'create' ? 'bg-green-100 text-green-800' :
                      log.action === 'update' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-6 py-4">{log.doc_slug}</td>
                  <td className="px-6 py-4">{log.user_name}</td>
                  <td className="px-6 py-4">
                    {new Date(log.timestamp).toLocaleString('zh-CN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
```

---

## 部署步骤

### 1. 前端修改

```bash
cd interview/apps/admin

# 创建 FastAPI 客户端封装
mkdir -p src/lib
# 复制上述代码到 src/lib/fastapi-client.ts

# 更新路由使用新封装
# 修改所有 API 调用使用 fastapi.getDocLogs() 等
```

### 2. 后端验证

```bash
cd /root/fastapi-web

# 查看实时日志，观察前端请求
make prod-logs

# 检查速率限制触发情况
docker logs fastapi-web-app --tail 100 | grep "429"
```

### 3. 测试验证

```typescript
// 在浏览器 Console 测试
import { getFastAPIToken, getCachedFastAPIToken } from '@/lib/fastapi';

// 首次请求（会请求新 Token）
console.log('首次请求:', await getFastAPIToken());

// 二次请求（使用缓存，不应触发 429）
console.log('二次请求:', await getFastAPIToken());
```

---

## 预期效果

### 修复前
```
POST /api/admin/fastapi-login 200 in 316ms
POST /api/admin/fastapi-login 429 in 67ms  ❌
POST /api/admin/fastapi-login 429 in 68ms  ❌
GET /api/fastapi/api/docs/logs 403 in 36ms   ❌
GET /api/fastapi/api/docs/stats 403 in 30ms  ❌
```

### 修复后
```
POST /api/admin/fastapi-login 200 in 316ms
GET /api/fastapi/api/docs/logs 200 in 45ms  ✅
GET /api/fastapi/api/docs/stats 200 in 32ms  ✅
GET /api/fastapi/api/docs/logs 200 in 38ms  ✅ (使用缓存，不登录）
```

---

## 监控建议

### 1. 添加前端监控

```typescript
// lib/monitor.ts

export function trackAPICall(path: string, status: number, cached: boolean) {
  if (typeof window === 'undefined') return;

  const event = new CustomEvent('APICall', {
    detail: { path, status, cached, timestamp: Date.now() }
  });

  window.dispatchEvent(event);

  // 发送到监控服务（可选）
  if (process.env.NODE_ENV === 'production') {
    // 上报到监控平台
  }
}

// 在 FastAPIClient.request() 中使用
trackAPICall(path, response.status, !!tokenPromise);
```

### 2. 添加后端监控

```python
# app/middleware.py

import logging

logger = logging.getLogger('fastapi.monitoring')

async def dispatch(self, request: Request, call_next):
    # ... 现有逻辑 ...

    # 记录 API 调用
    if settings.app_env == "production":
        logger.info(f"{request.method} {path} - {response.status_code} - {client_ip}")

    return response
```

---

## 总结

### 核心问题
1. 前端未缓存 FastAPI Token，频繁请求导致 429
2. Token 未正确传递到 API 请求头，导致 403

### 解决方案
1. ✅ **前端缓存 Token** - 优先方案，性能好，安全
2. ✅ **添加请求防抖** - 避免重复请求
3. ⚠️ **调整速率限制** - 备选方案，可能降低安全性

### 实施优先级
1. **高优先级**: 实现前端 Token 缓存（方案 1）
2. **中优先级**: 添加登录防抖（方案 2）
3. **低优先级**: 调整后端速率限制（方案 3）

---

## 参考文档

- [FastAPI 前端完整集成指南](./FRONTEND_INTEGRATION.md)
- [FastAPI API 文档](https://api.erishen.cn/docs)
