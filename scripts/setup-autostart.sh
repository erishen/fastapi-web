#!/bin/bash

# FastAPI Web 自动启动设置脚本
# 支持 Linux (systemd) 和 macOS (launchd)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
SERVICE_NAME="fastapi-web"

echo -e "${BLUE}FastAPI Web 自动启动设置${NC}"
echo "=================================="

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${YELLOW}检测到 Linux 系统，使用 systemd${NC}"

    # 检查是否为 root 用户
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}需要 root 权限来设置 systemd 服务${NC}"
        echo "请使用: sudo $0"
        exit 1
    fi

    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

    echo "创建 systemd 服务文件: $SERVICE_FILE"

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=FastAPI Web Docker Compose Service
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TimeoutStartSec=300
TimeoutStopSec=60
User=$SUDO_USER

[Install]
WantedBy=multi-user.target
EOF

    echo "重新加载 systemd 配置"
    systemctl daemon-reload

    echo "启用服务"
    systemctl enable "$SERVICE_NAME"

    echo "测试服务配置..."
    systemctl start "$SERVICE_NAME" 2>/dev/null || echo "服务启动测试失败，请检查配置"

    echo -e "${GREEN}systemd 服务已设置完成${NC}"
    echo ""
    echo "管理命令:"
    echo "  启动: sudo systemctl start $SERVICE_NAME"
    echo "  停止: sudo systemctl stop $SERVICE_NAME"
    echo "  状态: sudo systemctl status $SERVICE_NAME"
    echo "  日志: sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "配置文件: $SERVICE_FILE"

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}检测到 macOS 系统，使用 launchd${NC}"

    LAUNCHD_FILE="$HOME/Library/LaunchAgents/com.fastapi.web.plist"

    echo "创建 launchd 配置文件: $LAUNCHD_FILE"

    # 确保目录存在
    mkdir -p "$HOME/Library/LaunchAgents"

    cat > "$LAUNCHD_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fastapi.web</string>

    <key>ProgramArguments</key>
    <array>
        <string>docker</string>
        <string>compose</string>
        <string>up</string>
        <string>-d</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/auto-startup.log</string>

    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/auto-startup.error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

    echo "加载 launchd 服务"
    launchctl load "$LAUNCHD_FILE"

    echo -e "${GREEN}launchd 服务已设置完成${NC}"
    echo ""
    echo "管理命令:"
    echo "  启动: launchctl start com.fastapi.web"
    echo "  停止: launchctl stop com.fastapi.web"
    echo "  状态: launchctl list | grep fastapi"
    echo "  日志: tail -f ~/fastapi-web/logs/auto-startup.log"

else
    echo -e "${RED}不支持的操作系统: $OSTYPE${NC}"
    echo "目前支持: Linux (systemd) 和 macOS (launchd)"
    exit 1
fi

echo ""
echo -e "${GREEN}自动启动设置完成！${NC}"
echo "系统重启后，FastAPI Web 服务将自动启动。"
echo ""
echo -e "${YELLOW}注意:${NC}"
echo "1. 确保 Docker 守护进程设置为开机自启"
echo "2. 如果更改了项目路径，需要重新运行此脚本"
echo "3. 检查日志文件以确认服务正常启动"
