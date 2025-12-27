# 示例商品数据配置

该目录包含示例商品数据的配置文件。

## sample_items.json

示例商品数据配置文件，在 FastAPI 应用启动时自动加载。

### 配置结构

```json
{
  "enabled": true,        // 是否启用自动初始化
  "description": "...",   // 配置文件描述
  "items": [...]          // 商品数据列表
}
```

### 商品数据字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 商品名称，1-100字符 |
| `description` | string | 否 | 商品描述，最多1000字符 |
| `price` | number | 是 | 商品价格，必须大于0 |
| `is_offer` | boolean | 是 | 是否为特价商品 |

### 使用方法

#### 1. 添加新商品

在 `items` 数组中添加新的商品对象：

```json
{
  "name": "新商品名称",
  "description": "商品描述",
  "price": 999.00,
  "is_offer": false
}
```

#### 2. 禁用自动初始化

设置 `enabled` 为 `false`：

```json
{
  "enabled": false,
  ...
}
```

#### 3. 应用配置更改

修改配置文件后，需要重启 FastAPI 应用：

```bash
cd fastapi-web
make restart
```

### 重新初始化数据库

如果需要清空现有数据并重新初始化：

```bash
# 1. 清空商品表
docker compose exec app python -c "
from app.database import SessionLocal
from app.models import Item
db = SessionLocal()
db.query(Item).delete()
db.commit()
db.close()
"

# 2. 重启应用
make restart
```

### 注意事项

- 配置文件必须是有效的 JSON 格式
- 价格必须是正数
- 名称不能为空
- 建议定期备份此配置文件
