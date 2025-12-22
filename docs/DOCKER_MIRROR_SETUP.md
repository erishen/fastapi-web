# Docker 镜像源配置

如果在拉取 Docker 镜像时出现超时错误，可以配置国内镜像源。

## macOS 配置

### 方法 1：使用 Docker Desktop GUI

1. 打开 Docker Desktop
2. 点击菜单栏的 Docker 图标 → Preferences
3. 选择 Docker Engine
4. 在 JSON 编辑器中添加以下内容：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
  ]
}
```

5. 点击 Apply & Restart

### 方法 2：编辑配置文件

编辑 `~/.docker/daemon.json`：

```bash
# 如果文件不存在，创建它
mkdir -p ~/.docker

# 编辑文件
vim ~/.docker/daemon.json
```

添加以下内容：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
  ]
}
```

保存后重启 Docker。

## Linux 配置

编辑 `/etc/docker/daemon.json`：

```bash
sudo vim /etc/docker/daemon.json
```

添加以下内容：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
  ]
}
```

重启 Docker：

```bash
sudo systemctl restart docker
```

## Windows 配置

1. 右键点击 Docker Desktop 图标
2. 选择 Settings
3. 选择 Docker Engine
4. 在 JSON 编辑器中添加镜像源配置
5. 点击 Apply & Restart

## 验证配置

```bash
# 查看当前配置
docker info | grep -A 10 "Registry Mirrors"

# 测试拉取镜像
docker pull redis
```

## 可用的镜像源

| 镜像源 | 地址 | 说明 |
|--------|------|------|
| 中科大 | https://docker.mirrors.ustc.edu.cn | 稳定可靠 |
| 网易 | https://hub-mirror.c.163.com | 速度快 |
| 百度 | https://mirror.baidubce.com | 国内快 |
| 腾讯 | https://ccr.ccs.tencentyun.com | 国内快 |

## 常见问题

### Q: 配置后仍然超时？
A: 尝试以下步骤：
1. 重启 Docker Desktop
2. 检查网络连接
3. 尝试其他镜像源
4. 直接使用 `docker pull redis` 测试

### Q: 如何恢复默认配置？
A: 删除 `daemon.json` 中的 `registry-mirrors` 字段，或删除整个文件。

### Q: 多个镜像源的优先级？
A: 按照配置顺序，从上到下依次尝试。

## 相关资源

- [Docker 官方文档](https://docs.docker.com/docker-for-mac/install/)
- [Docker Hub 镜像加速](https://docs.docker.com/docker-hub/mirror/)
