.PHONY: help up down restart logs build clean status shell db redis backup restore health

# 颜色定义
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# 默认目标
.DEFAULT_GOAL := help

help: ## 显示帮助信息
	@echo "$(BLUE)FastAPI Web Docker 命令$(NC)"
	@echo ""
	@echo "$(GREEN)启动/停止命令:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)示例:$(NC)"
	@echo "  make up              # 启动所有服务"
	@echo "  make logs            # 查看实时日志"
	@echo "  make shell           # 进入应用容器"
	@echo "  make down            # 停止所有服务"

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

logs-mysql: ## 查看 MySQL 日志
	@docker compose logs -f mysql

logs-redis: ## 查看 Redis 日志
	@docker compose logs -f redis

build: ## 构建 Docker 镜像
	@echo "$(BLUE)[INFO]$(NC) 构建 Docker 镜像..."
	@docker compose build
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
	@curl -s http://localhost:$$(grep '^EXPOSE_PORT=' .env | cut -d= -f2)/health || echo "$(RED)✗ 未响应$(NC)"
	@echo ""
	@echo "$(BLUE)MySQL 数据库:$(NC)"
	@docker compose exec -T mysql mysqladmin ping -h localhost 2>/dev/null && echo "$(GREEN)✓ 正常$(NC)" || echo "$(RED)✗ 未响应$(NC)"
	@echo ""
	@echo "$(BLUE)Redis 缓存:$(NC)"
	@docker compose exec -T redis sh -c 'redis-cli -a "$$REDIS_PASSWORD" ping 2>/dev/null' && echo "$(GREEN)✓ 正常$(NC)" || echo "$(RED)✗ 未响应$(NC)"
	@echo ""

shell: ## 进入应用容器
	@docker compose exec app bash

db: ## 进入 MySQL 容器
	@docker compose exec mysql bash

redis: ## 进入 Redis 容器
	@docker compose exec redis sh

mysql-cli: ## 进入 MySQL 命令行
	@docker compose exec mysql mysql -uroot -ppassword fastapi_web

redis-cli: ## 进入 Redis 命令行
	@docker compose exec redis redis-cli

backup: ## 备份数据库
	@mkdir -p backups
	@echo "$(BLUE)[INFO]$(NC) 备份数据库..."
	@docker compose exec -T mysql mysqldump -uroot -ppassword fastapi_web > backups/mysql_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)[SUCCESS]$(NC) 数据库备份完成"

restore: ## 恢复数据库（使用: make restore FILE=backups/mysql_backup_xxx.sql）
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
		docker compose exec -T mysql mysql -uroot -ppassword fastapi_web < $(FILE); \
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
	@echo "$(BLUE)数据库连接:$(NC)"
	@echo "  MySQL:  localhost:$$(grep '^MYSQL_EXPOSE_PORT=' .env | cut -d= -f2)"
	@echo "  用户名: $$(grep '^MYSQL_USER=' .env | cut -d= -f2)"
	@echo "  密码:   $$(grep '^MYSQL_PASSWORD=' .env | cut -d= -f2)"
	@echo "  数据库: $$(grep '^MYSQL_DATABASE=' .env | cut -d= -f2)"
	@echo ""
	@echo "$(BLUE)Redis 连接:$(NC)"
	@echo "  地址: localhost:$$(grep '^REDIS_EXPOSE_PORT=' .env | cut -d= -f2)"
	@echo ""
	@echo "$(BLUE)常用命令:$(NC)"
	@echo "  make up              # 启动所有服务"
	@echo "  make logs            # 查看实时日志"
	@echo "  make shell           # 进入应用容器"
	@echo "  make health          # 检查服务健康状态"
	@echo "  make down            # 停止所有服务"
	@echo ""
