#!/bin/bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 默认值
MODE="up"
DETACH="-d"
BUILD=""
ENV_FILE=".env.docker"
COMPOSE_FILE="docker compose.yml"

# 帮助信息
show_help() {
    cat << EOF
${BLUE}FastAPI Web Docker 启动脚本${NC}

用法: $0 [命令] [选项]

命令:
  up              启动所有服务（默认）
  down            停止所有服务
  restart         重启所有服务
  logs            查看服务日志
  build           构建镜像
  clean           清理容器和卷
  status          查看服务状态
  shell           进入应用容器
  db              进入数据库容器
  redis           进入 Redis 容器
  backup          备份数据库
  restore         恢复数据库

选项:
  -f, --foreground    前台运行（不后台运行）
  -b, --build         启动前重新构建镜像
  -e, --env FILE      指定环境文件（默认: .env.docker）
  -h, --help          显示此帮助信息

示例:
  $0 up                           # 启动所有服务
  $0 up --build                   # 重新构建并启动
  $0 up --foreground              # 前台运行
  $0 logs -f                      # 查看实时日志
  $0 down                         # 停止所有服务
  $0 shell                        # 进入应用容器

EOF
}

# 打印信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_success "Docker 和 Docker Compose 已安装"
}

# 检查 Docker 守护进程
check_docker_daemon() {
    if ! docker info &> /dev/null; then
        print_error "Docker 守护进程未运行，请启动 Docker"
        exit 1
    fi
}

# 检查环境文件
check_env_file() {
    if [ ! -f "$PROJECT_DIR/$ENV_FILE" ]; then
        print_warning "环境文件 $ENV_FILE 不存在，使用默认配置"
        if [ -f "$PROJECT_DIR/.env" ]; then
            print_info "使用 .env 文件"
            ENV_FILE=".env"
        fi
    fi
}

# 启动服务
start_services() {
    print_info "启动 FastAPI Web 服务..."
    
    if [ -n "$BUILD" ]; then
        print_info "重新构建镜像..."
        docker compose -f "$COMPOSE_FILE" build
    fi
    
    if [ "$DETACH" = "-d" ]; then
        print_info "后台启动服务..."
        docker compose -f "$COMPOSE_FILE" up $DETACH
        sleep 3
        print_success "服务已启动"
        show_service_info
    else
        print_info "前台启动服务..."
        docker compose -f "$COMPOSE_FILE" up
    fi
}

# 停止服务
stop_services() {
    print_info "停止 FastAPI Web 服务..."
    docker compose -f "$COMPOSE_FILE" down
    print_success "服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启 FastAPI Web 服务..."
    docker compose -f "$COMPOSE_FILE" restart
    sleep 2
    print_success "服务已重启"
    show_service_info
}

# 查看日志
view_logs() {
    local service="$1"
    local follow="$2"
    
    if [ -z "$service" ]; then
        print_info "查看所有服务日志..."
        docker compose -f "$COMPOSE_FILE" logs $follow
    else
        print_info "查看 $service 服务日志..."
        docker compose -f "$COMPOSE_FILE" logs $follow "$service"
    fi
}

# 构建镜像
build_images() {
    print_info "构建 Docker 镜像..."
    docker compose -f "$COMPOSE_FILE" build
    print_success "镜像构建完成"
}

# 清理资源
clean_resources() {
    print_warning "即将删除所有容器和卷，此操作不可恢复！"
    read -p "确认删除？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "清理资源..."
        docker compose -f "$COMPOSE_FILE" down -v
        print_success "资源已清理"
    else
        print_info "已取消"
    fi
}

# 查看服务状态
show_status() {
    print_info "服务状态："
    docker compose -f "$COMPOSE_FILE" ps
}

# 进入应用容器
enter_app_shell() {
    print_info "进入应用容器..."
    docker compose -f "$COMPOSE_FILE" exec app bash
}

# 进入数据库容器
enter_db_shell() {
    print_info "进入数据库容器..."
    docker compose -f "$COMPOSE_FILE" exec mysql bash
}

# 进入 Redis 容器
enter_redis_shell() {
    print_info "进入 Redis 容器..."
    docker compose -f "$COMPOSE_FILE" exec redis sh
}

# 显示服务信息
show_service_info() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}FastAPI Web 服务已启动${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}服务地址:${NC}"
    echo "  FastAPI 应用: http://localhost:8080"
    echo "  API 文档:     http://localhost:8080/docs"
    echo "  Nginx 代理:   http://localhost:80"
    echo ""
    echo -e "${BLUE}数据库连接:${NC}"
    echo "  MySQL:  localhost:3306"
    echo "  用户名: root"
    echo "  密码:   password"
    echo "  数据库: fastapi_web"
    echo ""
    echo -e "${BLUE}Redis 连接:${NC}"
    echo "  地址: localhost:6379"
    echo ""
    echo -e "${BLUE}常用命令:${NC}"
    echo "  查看日志:     $0 logs -f"
    echo "  进入应用:     $0 shell"
    echo "  进入数据库:   $0 db"
    echo "  停止服务:     $0 down"
    echo ""
}

# 备份数据库
backup_database() {
    local backup_dir="$PROJECT_DIR/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/mysql_backup_$timestamp.sql"
    
    mkdir -p "$backup_dir"
    
    print_info "备份数据库到 $backup_file..."
    docker compose -f "$COMPOSE_FILE" exec -T mysql mysqldump \
        -uroot -ppassword fastapi_web > "$backup_file"
    
    print_success "数据库备份完成: $backup_file"
}

# 恢复数据库
restore_database() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        print_error "请指定备份文件路径"
        echo "用法: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    print_warning "即将恢复数据库，此操作将覆盖现有数据！"
    read -p "确认恢复？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "恢复数据库..."
        docker compose -f "$COMPOSE_FILE" exec -T mysql mysql \
            -uroot -ppassword fastapi_web < "$backup_file"
        print_success "数据库恢复完成"
    else
        print_info "已取消"
    fi
}

# 主函数
main() {
    # 解析命令
    if [ $# -eq 0 ]; then
        MODE="up"
    else
        MODE="$1"
        shift
    fi
    
    # 解析选项
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--foreground)
                DETACH=""
                shift
                ;;
            -b|--build)
                BUILD="true"
                shift
                ;;
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                # 对于某些命令，剩余参数可能是子命令参数
                break
                ;;
        esac
    done
    
    # 检查 Docker
    check_docker
    check_docker_daemon
    check_env_file
    
    # 进入项目目录
    cd "$PROJECT_DIR"
    
    # 执行命令
    case $MODE in
        up)
            start_services
            ;;
        down)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs "$@"
            ;;
        build)
            build_images
            ;;
        clean)
            clean_resources
            ;;
        status)
            show_status
            ;;
        shell)
            enter_app_shell
            ;;
        db)
            enter_db_shell
            ;;
        redis)
            enter_redis_shell
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database "$1"
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "未知命令: $MODE"
            echo "使用 '$0 --help' 查看帮助信息"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
