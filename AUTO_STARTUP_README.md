# FastAPI Web 自动启动配置

本项目支持系统重启后自动启动 Docker 服务。

## 📋 当前状态

✅ **Docker 容器级别**: 已配置 `restart: always` - Docker 重启时自动启动容器
❓ **系统级别**: 需要额外配置系统服务

## 🚀 自动启动设置

### 方法 1: 使用自动配置脚本（推荐）

```bash
# Linux
sudo ./scripts/setup-autostart.sh

# macOS
./scripts/setup-autostart.sh
```

### 方法 2: 手动配置

#### Linux (systemd)
```bash
# 复制服务文件
sudo cp scripts/auto-startup.service /etc/systemd/system/fastapi-web.service

# 重新加载配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable fastapi-web

# 启动服务
sudo systemctl start fastapi-web
```

#### macOS (launchd)
```bash
# 复制 plist 文件（修改路径）
cp scripts/com.fastapi.web.plist ~/Library/LaunchAgents/

# 编辑 WorkingDirectory 路径
vim ~/Library/LaunchAgents/com.fastapi.web.plist

# 加载服务
launchctl load ~/Library/LaunchAgents/com.fastapi.web.plist
```

### 方法 3: Docker Desktop

如果使用 Docker Desktop：
1. 打开 Docker Desktop
2. 进入 Settings → General
3. 启用 "Start Docker Desktop when you log in"

## 📊 管理命令

### Linux (systemd)
```bash
# 状态检查
sudo systemctl status fastapi-web

# 启动/停止
sudo systemctl start fastapi-web
sudo systemctl stop fastapi-web

# 查看日志
sudo journalctl -u fastapi-web -f
```

### macOS (launchd)
```bash
# 状态检查
launchctl list | grep fastapi

# 启动/停止
launchctl start com.fastapi.web
launchctl stop com.fastapi.web

# 查看日志
tail -f ~/fastapi-web/logs/auto-startup.log
```

## 🔍 故障排除

### 服务没有启动
```bash
# 检查 Docker 是否运行
docker ps

# 检查服务状态
systemctl status fastapi-web  # Linux
launchctl list | grep fastapi  # macOS

# 查看详细日志
docker-compose logs
```

### 路径问题
如果移动了项目目录，需要：
1. 更新服务配置文件中的路径
2. 重新加载服务配置

### 权限问题
确保用户有执行 Docker 命令的权限。

## ⚠️ 注意事项

- **安全**: 自动启动服务可能影响系统安全
- **资源**: 确保系统有足够资源运行服务
- **网络**: 服务启动可能需要网络连接
- **日志**: 定期检查日志文件

## 🔄 取消自动启动

### Linux
```bash
sudo systemctl disable fastapi-web
sudo systemctl stop fastapi-web
sudo rm /etc/systemd/system/fastapi-web.service
sudo systemctl daemon-reload
```

### macOS
```bash
launchctl unload ~/Library/LaunchAgents/com.fastapi.web.plist
rm ~/Library/LaunchAgents/com.fastapi.web.plist
```
