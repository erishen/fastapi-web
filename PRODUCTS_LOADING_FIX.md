# 商品展示加载问题修复指南

## 问题描述
访问 http://localhost:3000/ 时，商品展示一开始会显示"加载中..."，需要刷新页面才能显示商品数据。

## 已完成的修复

### 1. 前端组件优化 (`apps/web/src/components/ProductsDisplay.tsx`)

- ✅ 添加了自动重试机制（最多3次，间隔1秒）
- ✅ 改进了错误处理和日志输出
- ✅ 添加了 500ms 延迟确保后端完全启动
- ✅ 改进了加载状态显示（带旋转动画）
- ✅ 在错误时显示重试按钮
- ✅ 更详细的错误信息

### 2. 端口配置统一 (`packages/config/src/api.ts`)

- ✅ 将 FastAPI 默认端口从 8081 改为 8082，与实际配置保持一致

### 3. 自动初始化数据 (`fastapi-web/app/factory.py`)

- ✅ 在应用启动时自动初始化示例商品数据（从配置文件读取）
- ✅ 添加了 10 个示例商品（可通过配置文件修改）
- ✅ 自动检测是否已有数据，避免重复插入
- ✅ 支持禁用自动初始化功能

## 使用步骤

### 1. 初始化数据库（首次运行）

```bash
cd fastapi-web

# 创建数据库（如果还没创建）
make init-db
```

### 2. 配置示例商品（可选）

编辑 `app/data/sample_items.json` 文件来配置示例商品：

```json
{
  "enabled": true,  // 是否启用自动初始化
  "description": "示例商品数据配置文件",
  "items": [
    {
      "name": "商品名称",
      "description": "商品描述",
      "price": 999.00,
      "is_offer": true  // 是否为特价商品
    }
  ]
}
```

### 3. 启动 FastAPI 后端（自动初始化数据）

```bash
cd fastapi-web

# 启动服务，会自动初始化示例商品数据
make up
```

```bash
cd fastapi-web

# 启动服务
make up

# 查看日志确认启动成功
make logs
```

### 3. 启动前端应用

```bash
cd interview

# 启动 web 应用
pnpm --filter web dev
```

### 4. 访问应用

打开浏览器访问：http://localhost:3000/

## 故障排查

### 问题：仍然显示"加载中..."

1. **检查 FastAPI 后端是否运行**
   ```bash
   curl http://localhost:8082/health
   ```

2. **检查数据库是否有数据**
   ```bash
   cd fastapi-web
   docker compose exec app python -c "
   from app.database import SessionLocal
   from app.models import Item
   db = SessionLocal()
   count = db.query(Item).count()
   print(f'商品数量: {count}')
   db.close()
   "
   ```

3. **查看启动日志**
   ```bash
   cd fastapi-web
   make logs
   ```
   应该看到类似这样的日志：
   ```
   📦 初始化示例商品数据...
   ✓ 成功初始化 10 个示例商品
   ```

4. **查看浏览器控制台日志**
   - 打开浏览器开发者工具（F12）
   - 查看 Console 和 Network 标签
   - 检查 `/api/fastapi/items` 请求的状态和响应

5. **重试加载**
   - 点击页面上的"刷新"按钮
   - 或使用浏览器刷新（F5 或 Cmd+R）

## 技术细节

### 修复的核心问题

1. **时序问题**：前端组件挂载时，FastAPI 后端可能还未完全启动或数据库连接未就绪
   - 解决方案：添加 500ms 延迟 + 自动重试机制

2. **错误处理不完善**：请求失败后没有适当的重试机制
   - 解决方案：实现自动重试（最多3次）和手动重试按钮

3. **端口配置不一致**：代码中默认端口与实际配置不一致
   - 解决方案：统一端口配置为 8082

### 代码改进

```typescript
// 自动重试机制
const loadProducts = async (retryCount = 0) => {
  setLoading(true)
  setError(null)
  try {
    const response = await fetch('/api/fastapi/items')
    const data = await response.json()
    if (response.ok) {
      setProducts(data || [])
      setLoading(false)
    } else {
      throw new Error(...)
    }
  } catch (err) {
    if (retryCount < 3) {
      setTimeout(() => loadProducts(retryCount + 1), 1000)
    } else {
      setError(...)
      setLoading(false)
    }
  }
}

// 延迟加载
useEffect(() => {
  const timer = setTimeout(() => {
    loadProducts()
  }, 500)
  return () => clearTimeout(timer)
}, [])
```

## 配置说明

### 商品数据配置文件

配置文件位置：`app/data/sample_items.json`

#### 配置选项

| 字段 | 类型 | 说明 |
|------|------|------|
| `enabled` | boolean | 是否启用自动初始化（默认：true）|
| `description` | string | 配置文件描述 |
| `items` | array | 商品数据列表 |

#### 商品字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 商品名称（1-100字符）|
| `description` | string | 否 | 商品描述（最多1000字符）|
| `price` | number | 是 | 商品价格（必须大于0）|
| `is_offer` | boolean | 是 | 是否为特价商品 |

#### 禁用自动初始化

在 `sample_items.json` 中设置 `enabled` 为 `false`：

```json
{
  "enabled": false,
  "description": "示例商品数据配置文件",
  "items": [...]
}
```

#### 修改商品数据

1. 编辑 `app/data/sample_items.json`
2. 添加、修改或删除商品项
3. 重启 FastAPI 应用：
   ```bash
   make restart
   ```

#### 清空数据库重新初始化

如果想要重新初始化商品数据：

```bash
# 1. 清空商品表
cd fastapi-web
docker compose exec app python -c "
from app.database import SessionLocal
from app.models import Item
db = SessionLocal()
db.query(Item).delete()
db.commit()
print('已清空商品表')
db.close()
"

# 2. 重启应用（会重新初始化）
make restart
```

## 相关文件

- `apps/web/src/components/ProductsDisplay.tsx` - 商品展示组件
- `packages/config/src/api.ts` - API 配置
- `fastapi-web/app/factory.py` - 应用初始化逻辑（包含数据初始化）
- `fastapi-web/app/data/sample_items.json` - 示例商品配置文件
- `fastapi-web/app/routers/items.py` - 商品 API 路由
- `fastapi-web/app/models.py` - 数据模型
