# Docker 镜像构建速度优化指南

## 快速部署命令

### 1. 日常更新（推荐）
只重启容器，不重新构建镜像，速度最快：

```bash
make prod-rebuild
```

**适用场景：** 代码变更、配置文件更新（由于使用了 volume 挂载）

**耗时：** 5-10 秒


### 2. 首次部署或依赖变更
使用缓存的构建，较慢但可接受：

```bash
make prod-build
```

**适用场景：** 首次部署、requirements.txt 变更

**耗时：** 1-3 分钟（取决于网络）


### 3. 完全重新构建
不使用缓存，最慢：

```bash
make prod-build-no-cache
```

**适用场景：** 依赖冲突、缓存问题

**耗时：** 3-5 分钟


## 构建速度对比

| 命令 | 首次 | 依赖不变 | 代码变更 |
|-------|--------|-----------|----------|
| prod-rebuild | N/A | ✅ 5-10秒 | ✅ 5-10秒 |
| prod-build | 1-3分钟 | 10-30秒 | 10-30秒 |
| prod-build-no-cache | 3-5分钟 | 3-5分钟 | 3-5分钟 |


## 优化建议

### 1. 使用优化的 Dockerfile

如果构建仍然太慢，可以使用优化的 Dockerfile：

```bash
# 备份原文件
cp Dockerfile Dockerfile.backup

# 使用优化的 Dockerfile
cp Dockerfile.optimized Dockerfile

# 重新构建
make prod-build
```

**优化点：**
- 使用 `python:3.10-slim` 基础镜像（更小、更快）
- 合并 RUN 层，减少层数
- 优化 apt-get 清理


### 2. 使用 Docker BuildKit 加速

在宿主机设置环境变量：

```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# 然后正常构建
make prod-build
```


### 3. 使用国内镜像源（阿里云服务器）

创建 `daemon.json` 配置：

```bash
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF

# 重启 Docker
sudo systemctl restart docker
```


### 4. pip 使用国内源

编辑 `requirements.txt`，添加源：

```bash
-i https://pypi.tuna.tsinghua.edu.cn/simple
```

或修改 `/etc/pip.conf`：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
``


## 工作流程推荐

### 开发阶段
```bash
# 本地开发（macOS）
make up

# 测试
curl http://localhost:8082/health
```


### 部署到生产环境
```bash
# 阿里云服务器

# 1. 确保最新代码
git pull

# 2. 如果只是代码变更，快速重启
make prod-rebuild

# 3. 如果依赖变更，构建镜像
make prod-build

# 4. 查看日志
make prod-logs

# 5. 验证
make prod-health
```


## 故障排查

### 构建卡在某个步骤

```bash
# 查看 Docker 构建详情
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker compose -f docker-compose.prod.yml build
```


### pip 下载慢

使用国内源：

```bash
# 临时使用
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### apt-get 更新慢

使用国内源（修改 Dockerfile）：

```dockerfile
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
```
