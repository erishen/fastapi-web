FROM python:3.10

WORKDIR /app

# 构建参数
ARG PORT=8080

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码（排除 .env 文件）
COPY .dockerignore .dockerignore
COPY . .

# 删除镜像内的 .env 文件（使用环境变量代替）
RUN if [ -f .env ]; then rm .env; fi

# 创建日志目录
RUN mkdir -p logs

# 复制并设置启动脚本权限
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 复制并设置健康检查脚本权限
COPY healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# 暴露端口
EXPOSE ${PORT}

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 启动应用
ENTRYPOINT ["/app/entrypoint.sh"]
