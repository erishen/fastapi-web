# 🚀 快速开始

## 方法一：使用 MySQL 数据库（推荐）

### 1. 初始化 MySQL 数据库
```bash
# 确保 MySQL 服务运行
brew services start mysql  # macOS
# 或 sudo systemctl start mysql  # Linux

# 初始化数据库
./scripts/init_mysql.sh
```

### 2. 设置 Conda 环境
```bash
# 运行 Conda 环境设置脚本
./scripts/setup_env.sh

# 激活 Conda 环境
conda activate fastapi-web
```

### 3. 运行项目
```bash
python -m app.main
```

## 方法二：使用 environment.yml 文件
```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate fastapi-web

# 初始化数据库
./scripts/init_mysql.sh

# 运行项目
python -m app.main
```

## 方法三：使用 SQLite（简单测试）
```bash
# 修改 .env 文件中的数据库配置
# DATABASE_URL=sqlite:///./app.db

# 运行项目
python -m app.main
```

## 其他运行方式
```bash
# 使用 run.sh 脚本
./run.sh

# 使用 PM2 部署（生产环境）
./scripts/startup.sh

# 停止 PM2 服务
./scripts/shutdown.sh
```

## 📊 API 文档
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- 健康检查: http://localhost:8080/health

## 🔧 数据库配置

### MySQL 配置
```bash
# .env 文件中的配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/fastapi_web
```

### 主要配置项
- `DATABASE_URL`: 数据库连接字符串
- `PORT`: 服务端口（默认8080）
- `APP_ENV`: 应用环境（development/production）

## 🗄️ 数据库管理

### MySQL 操作
```bash
# 连接数据库
mysql -u root -p

# 查看数据库
SHOW DATABASES;

# 使用数据库
USE fastapi_web;

# 查看表结构
DESCRIBE items;

# 查看数据
SELECT * FROM items;
```

## 🐍 Conda 环境管理
```bash
# 查看所有环境
conda env list

# 删除环境
conda env remove -n fastapi-web

# 导出环境
conda env export > environment.yml

# 更新环境
conda env update -f environment.yml
```

## 🔧 API 功能

### 商品管理 API
- `GET /items/` - 获取商品列表（支持分页）
- `GET /items/search` - 搜索商品
- `GET /items/{id}` - 获取单个商品
- `POST /items/` - 创建商品
- `PUT /items/{id}` - 更新商品
- `DELETE /items/{id}` - 删除商品

### 示例请求
```bash
# 创建商品
curl -X POST "http://localhost:8080/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试商品",
    "price": 99.99,
    "is_offer": true,
    "description": "这是一个测试商品"
  }'

# 获取商品列表
curl "http://localhost:8080/items/?skip=0&limit=10"

# 搜索商品
curl "http://localhost:8080/items/search?keyword=测试"
``` 

