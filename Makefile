.PHONY: help up down restart logs build clean status shell db redis backup restore health autostart mysql-cli-host redis-cli-host prod-up prod-down prod-restart prod-logs prod-build

# 颜色定义 - 根据环境变量决定是否显示颜色
NO_COLOR := $(shell echo $$NO_COLOR)
FORCE_COLOR := $(shell echo $$FORCE_COLOR)

ifeq ($(NO_COLOR),1)
    BLUE :=
    GREEN :=
    YELLOW :=
    RED :=
    NC :=
else ifeq ($(FORCE_COLOR),1)
    BLUE := \033[0;34m
    GREEN := \033[0;32m
    YELLOW := \033[1;33m
    RED := \033[0;31m
    NC := \033[0m # No Color
else
    # 默认启用颜色（macOS 友好）
    BLUE := \033[0;34m
    GREEN := \033[0;32m
    YELLOW := \033[1;33m
    RED := \033[0;31m
    NC := \033[0m # No Color
endif

# 默认目标
.DEFAULT_GOAL := help

help: ## 显示帮助信息
	@echo "$(BLUE)FastAPI Web Docker 命令$(NC)"
	@echo ""
	@echo "$(GREEN)启动/停止命令:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-18s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)示例:$(NC)"
	@echo "  make up              # 启动所有服务"
	@echo "  make up-build        # 重新构建并启动（使用缓存）"
	@echo "  make up-build-nocache # 强制重新构建并启动（不使用缓存）"
	@echo "  make logs            # 查看实时日志"
	@echo "  make shell           # 进入应用容器"
	@echo "  make mysql-cli       # 连接 MySQL 命令行（宿主机）"
	@echo "  make redis-cli       # 连接 Redis 命令行（宿主机）"
	@echo "  make down            # 停止所有服务"
	@echo ""
	@echo "$(YELLOW)生产环境命令（阿里云）:$(NC)"
	@echo "  make prod-up         # 启动生产环境（使用 docker-compose.prod.yml）"
	@echo "  make prod-down       # 停止生产环境"
	@echo "  make prod-restart    # 重启生产环境"
	@echo "  make prod-logs       # 查看生产环境日志"
	@echo "  make prod-health     # 检查生产环境健康状态"
	@echo ""
	@echo "$(YELLOW)注意: MySQL 和 Redis 运行在宿主机，不通过 Docker 管理$(NC)"

up: ## 启动所有服务
	@echo "$(BLUE)[INFO]$(NC) 启动 FastAPI Web 服务..."
	@docker compose up -d
	@sleep 2
	@echo "$(GREEN)[SUCCESS]$(NC) 服务已启动"
	@make health

up-build: ## 重新构建并启动服务
	@echo "$(BLUE)[INFO]$(NC) 重新构建镜像并启动..."
	@docker compose up -d --build
	@sleep 2
	@echo "$(GREEN)[SUCCESS]$(NC) 服务已启动"
	@make health

up-build-nocache: ## 重新构建并启动服务（不使用缓存）
	@echo "$(BLUE)[INFO]$(NC) 强制重新构建镜像..."
	@docker compose build --no-cache
	@echo "$(BLUE)[INFO]$(NC) 启动服务..."
	@docker compose up -d
	@sleep 2
	@echo "$(GREEN)[SUCCESS]$(NC) 服务已启动"
	@make health

up-foreground: ## 前台启动服务（显示日志）
	@echo "$(BLUE)[INFO]$(NC) 前台启动服务..."
	@docker compose up

down: ## 停止所有服务
	@echo "$(BLUE)[INFO]$(NC) 停止 FastAPI Web 服务..."
	@docker compose down
	@echo "$(GREEN)[SUCCESS]$(NC) 服务已停止"

restart: ## 重启所有服务
	@echo "$(BLUE)[INFO]$(NC) 重启 FastAPI Web 服务..."
	@docker compose restart
	@sleep 2
	@echo "$(GREEN)[SUCCESS]$(NC) 服务已重启"
	@make health

logs: ## 查看实时日志
	@docker compose logs -f

logs-app: ## 查看应用日志
	@docker compose logs -f app

logs-mysql: ## 查看 MySQL 日志 (宿主机)
	@echo "$(YELLOW)[INFO]$(NC) MySQL 运行在宿主机，使用以下命令查看日志："
	@echo "  macOS:  brew services list | grep mysql"
	@echo "  tail -f /usr/local/var/mysql/*.err"

logs-redis: ## 查看 Redis 日志 (宿主机)
	@echo "$(YELLOW)[INFO]$(NC) Redis 运行在宿主机，使用以下命令查看日志："
	@echo "  macOS:  brew services list | grep redis"
	@echo "  tail -f /usr/local/var/log/redis.log"

build: ## 构建 Docker 镜像
	@echo "$(BLUE)[INFO]$(NC) 构建 Docker 镜像..."
	@docker compose build
	@echo "$(GREEN)[SUCCESS]$(NC) 镜像构建完成"

build-nocache: ## 构建 Docker 镜像（不使用缓存）
	@echo "$(BLUE)[INFO]$(NC) 强制构建 Docker 镜像..."
	@docker compose build --no-cache
	@echo "$(GREEN)[SUCCESS]$(NC) 镜像构建完成"

clean: ## 清理容器和卷（谨慎操作）
	@echo "$(YELLOW)[WARNING]$(NC) 即将删除所有容器和卷"
	@read -p "确认删除？(y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)[INFO]$(NC) 清理资源..."; \
		docker compose down -v; \
		echo "$(GREEN)[SUCCESS]$(NC) 资源已清理"; \
	else \
		echo "$(BLUE)[INFO]$(NC) 已取消"; \
	fi

status: ## 查看服务状态
	@echo "$(BLUE)服务状态:$(NC)"
	@docker compose ps

health: ## 检查服务健康状态
	@echo "$(BLUE)[INFO]$(NC) 检查服务健康状态..."
	@echo ""
	@echo "$(BLUE)FastAPI 应用:$(NC)"
	@curl -s http://localhost:$$(grep '^PORT=' .env 2>/dev/null | cut -d= -f2)/health 2>/dev/null | jq -r 'if .status == "healthy" then "✓ 正常 (数据库: \(.database))" else "✗ 异常" end' 2>/dev/null || echo "$(RED)✗ 未响应$(NC)"
	@echo ""
	@echo "$(BLUE)MySQL 数据库 (宿主机):$(NC)"
	@if mysqladmin ping -h 127.0.0.1 -P $$(grep '^MYSQL_PORT=' .env 2>/dev/null | cut -d= -f2) -u $$(grep '^MYSQL_USER=' .env 2>/dev/null | cut -d= -f2) -p$$(grep '^MYSQL_PASSWORD=' .env 2>/dev/null | cut -d= -f2) 2>/dev/null; then \
		echo "$(GREEN)✓ 正常$(NC)"; \
	else \
		echo "$(RED)✗ 未响应$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Redis 缓存 (宿主机):$(NC)"
	@if redis-cli -h 127.0.0.1 -p 6379 -n 0 -a redis_password ping 2>/dev/null | grep -q PONG; then \
		echo "$(GREEN)✓ 正常$(NC)"; \
	else \
		echo "$(RED)✗ 未响应$(NC)"; \
	fi
	@echo ""

shell: ## 进入应用容器
	@docker compose exec app bash

db: ## 连接到宿主机 MySQL
	@echo "$(YELLOW)[INFO]$(NC) MySQL 运行在宿主机，请使用以下命令连接："
	@echo "  mysql -h 127.0.0.1 -P $$(grep '^MYSQL_PORT=' .env 2>/dev/null | cut -d= -f2) -u $$(grep '^MYSQL_USER=' .env 2>/dev/null | cut -d= -f2) -p $$(grep '^MYSQL_DATABASE=' .env 2>/dev/null | cut -d= -f2)"

redis: ## 连接到宿主机 Redis
	@echo "$(YELLOW)[INFO]$(NC) Redis 运行在宿主机，请使用以下命令连接："
	@echo "  redis-cli -h 127.0.0.1 -p $$(grep '^REDIS_PORT=' .env 2>/dev/null | cut -d= -f2) -n $$(grep '^REDIS_DB=' .env 2>/dev/null | cut -d= -f2)"

mysql-cli: ## 连接到 MySQL 命令行 (宿主机)
	@mysql -h 127.0.0.1 -P $$(grep '^MYSQL_PORT=' .env 2>/dev/null | cut -d= -f2) -u $$(grep '^MYSQL_USER=' .env 2>/dev/null | cut -d= -f2) -p$$(grep '^MYSQL_PASSWORD=' .env 2>/dev/null | cut -d= -f2) $$(grep '^MYSQL_DATABASE=' .env 2>/dev/null | cut -d= -f2)

mysql-cli-host: ## 使用 root 连接到宿主机 MySQL
	@mysql -h 127.0.0.1 -P $$(grep '^MYSQL_PORT=' .env 2>/dev/null | cut -d= -f2) -u root -p $$(grep '^MYSQL_DATABASE=' .env 2>/dev/null | cut -d= -f2)

redis-cli: ## 连接到 Redis 命令行 (宿主机)
	@redis-cli -h 127.0.0.1 -p $$(grep '^REDIS_PORT=' .env 2>/dev/null | cut -d= -f2) -n $$(grep '^REDIS_DB=' .env 2>/dev/null | cut -d= -f2)

redis-cli-host: ## 连接到宿主机 Redis (本地)
	@redis-cli -h 127.0.0.1 -p $$(grep '^REDIS_PORT=' .env 2>/dev/null | cut -d= -f2) -n 0

backup: ## 备份数据库 (宿主机)
	@mkdir -p backups
	@echo "$(BLUE)[INFO]$(NC) 备份数据库..."
	@mysqldump -h 127.0.0.1 -P $$(grep '^MYSQL_PORT=' .env 2>/dev/null | cut -d= -f2) -u $$(grep '^MYSQL_USER=' .env 2>/dev/null | cut -d= -f2) -p$$(grep '^MYSQL_PASSWORD=' .env 2>/dev/null | cut -d= -f2) $$(grep '^MYSQL_DATABASE=' .env 2>/dev/null | cut -d= -f2) > backups/mysql_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)[SUCCESS]$(NC) 数据库备份完成"

restore: ## 恢复数据库 (使用: make restore FILE=backups/mysql_backup_xxx.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)[ERROR]$(NC) 请指定备份文件: make restore FILE=backups/mysql_backup_xxx.sql"; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "$(RED)[ERROR]$(NC) 备份文件不存在: $(FILE)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)[WARNING]$(NC) 即将恢复数据库，此操作将覆盖现有数据"
	@read -p "确认恢复？(y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)[INFO]$(NC) 恢复数据库..."; \
		mysql -h 127.0.0.1 -P $$(grep '^MYSQL_PORT=' .env 2>/dev/null | cut -d= -f2) -u $$(grep '^MYSQL_USER=' .env 2>/dev/null | cut -d= -f2) -p$$(grep '^MYSQL_PASSWORD=' .env 2>/dev/null | cut -d= -f2) $$(grep '^MYSQL_DATABASE=' .env 2>/dev/null | cut -d= -f2) < $(FILE); \
		echo "$(GREEN)[SUCCESS]$(NC) 数据库恢复完成"; \
	else \
		echo "$(BLUE)[INFO]$(NC) 已取消"; \
	fi

prune: ## 清理未使用的 Docker 资源
	@echo "$(BLUE)[INFO]$(NC) 清理未使用的 Docker 资源..."
	@docker system prune -f
	@echo "$(GREEN)[SUCCESS]$(NC) 清理完成"

version: ## 显示版本信息
	@echo "$(BLUE)Docker 版本:$(NC)"
	@docker --version
	@echo "$(BLUE)Docker Compose 版本:$(NC)"
	@docker compose --version

info: ## 显示服务信息
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)FastAPI Web 服务信息$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "$(BLUE)服务地址:$(NC)"
	@echo "  FastAPI 应用: http://localhost:$$(grep '^EXPOSE_PORT=' .env | cut -d= -f2)"
	@echo "  API 文档:     http://localhost:$$(grep '^EXPOSE_PORT=' .env | cut -d= -f2)/docs"
	@echo ""
	@echo "$(BLUE)数据库连接 (宿主机):$(NC)"
	@echo "  MySQL:  127.0.0.1:$$(grep '^MYSQL_PORT=' .env | cut -d= -f2)"
	@echo "  用户名: $$(grep '^MYSQL_USER=' .env | cut -d= -f2)"
	@echo "  数据库: $$(grep '^MYSQL_DATABASE=' .env | cut -d= -f2)"
	@echo ""
	@echo "$(BLUE)Redis 连接 (宿主机):$(NC)"
	@echo "  地址: 127.0.0.1:$$(grep '^REDIS_PORT=' .env | cut -d= -f2)"
	@echo "  DB:   $$(grep '^REDIS_DB=' .env | cut -d= -f2)"
	@echo ""
	@echo "$(BLUE)常用命令:$(NC)"
	@echo "  make up              # 启动所有服务"
	@echo "  make logs            # 查看实时日志"
	@echo "  make shell           # 进入应用容器"
	@echo "  make mysql-cli       # 连接 MySQL 命令行"
	@echo "  make redis-cli       # 连接 Redis 命令行"
	@echo "  make health          # 检查服务健康状态"
	@echo "  make down            # 停止所有服务"
	@echo "  make info            # 显示服务信息"
	@echo ""

autostart: ## 设置系统自动启动
	@echo "$(BLUE)[INFO]$(NC) 设置系统自动启动..."
	@if [[ "$$OSTYPE" == "linux-gnu"* ]]; then \
		echo "$(YELLOW)检测到 Linux 系统$(NC)"; \
		if [[ $$EUID -eq 0 ]]; then \
			chmod +x scripts/setup-autostart.sh && ./scripts/setup-autostart.sh; \
		else \
			echo "$(RED)需要 root 权限，请使用: sudo make autostart$(NC)"; \
			exit 1; \
		fi \
	elif [[ "$$OSTYPE" == "darwin"* ]]; then \
		echo "$(YELLOW)检测到 macOS 系统$(NC)"; \
		chmod +x scripts/setup-autostart.sh && ./scripts/setup-autostart.sh; \
	else \
		echo "$(RED)不支持的操作系统$(NC)"; \
		echo "请查看 AUTO_STARTUP_README.md 了解手动配置方法"; \
		exit 1; \
	fi
	@echo "$(GREEN)[SUCCESS]$(NC) 自动启动设置完成"

# ================================
# 🚀 生产环境命令（阿里云）
# ================================

prod-up: ## 启动生产环境服务（使用 docker-compose.prod.yml）
	@echo "$(BLUE)[INFO]$(NC) 启动生产环境服务..."
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)[WARNING]$(NC) .env 文件不存在，请先创建配置文件"; \
		exit 1; \
	fi
	@cp .env .env.backup 2>/dev/null || true
	@if [ -f .env.aliyun ]; then \
		echo "$(BLUE)[INFO]$(NC) 使用阿里云配置文件 .env.aliyun"; \
		cp .env.aliyun .env; \
	fi
	@docker compose -f docker-compose.prod.yml up -d
	@sleep 3
	@echo "$(GREEN)[SUCCESS]$(NC) 生产环境服务已启动"
	@make prod-health

prod-down: ## 停止生产环境服务
	@echo "$(BLUE)[INFO]$(NC) 停止生产环境服务..."
	@docker compose -f docker-compose.prod.yml down
	@echo "$(GREEN)[SUCCESS]$(NC) 生产环境服务已停止"

prod-restart: ## 重启生产环境服务
	@echo "$(BLUE)[INFO]$(NC) 重启生产环境服务..."
	@docker compose -f docker-compose.prod.yml restart
	@sleep 3
	@echo "$(GREEN)[SUCCESS]$(NC) 生产环境服务已重启"
	@make prod-health

prod-logs: ## 查看生产环境日志
	@docker compose -f docker-compose.prod.yml logs -f

prod-build: ## 构建生产环境镜像
	@echo "$(BLUE)[INFO]$(NC) 构建生产环境镜像..."
	@docker compose -f docker-compose.prod.yml build
	@echo "$(GREEN)[SUCCESS]$(NC) 镜像构建完成"

prod-health: ## 检查生产环境健康状态
	@echo "$(BLUE)[INFO]$(NC) 检查生产环境健康状态..."
	@echo ""
	@echo "$(BLUE)FastAPI 应用 (端口 $(shell grep '^PORT=' .env 2>/dev/null | cut -d= -f2))$(NC):"
	@curl -s http://localhost:$$(grep '^PORT=' .env 2>/dev/null | cut -d= -f2)/health 2>/dev/null | jq -r 'if .status == "healthy" then "✓ 正常 (数据库: \(.database))" else "✗ 异常" end' 2>/dev/null || echo "$(RED)✗ 未响应$(NC)"
	@echo ""
	@echo "$(BLUE)MySQL 数据库 (宿主机):$(NC)"
	@if mysqladmin ping -h $$(grep '^MYSQL_HOST=' .env 2>/dev/null | cut -d= -f2) -P $$(grep '^MYSQL_PORT=' .env 2>/dev/null | cut -d= -f2) -u $$(grep '^MYSQL_USER=' .env 2>/dev/null | cut -d= -f2) -p$$(grep '^MYSQL_PASSWORD=' .env 2>/dev/null | cut -d= -f2) 2>/dev/null; then \
		echo "$(GREEN)✓ 正常$(NC)"; \
	else \
		echo "$(RED)✗ 未响应$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Redis 缓存 (宿主机):$(NC)"
	@if redis-cli -h $$(grep '^REDIS_HOST=' .env 2>/dev/null | cut -d= -f2) -p $$(grep '^REDIS_PORT=' .env 2>/dev/null | cut -d= -f2) -n 0 -a $$(grep '^REDIS_PASSWORD=' .env 2>/dev/null | cut -d= -f2) ping 2>/dev/null | grep -q PONG; then \
		echo "$(GREEN)✓ 正常$(NC)"; \
	else \
		echo "$(RED)✗ 未响应$(NC)"; \
	fi
	@echo ""
