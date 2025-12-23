@echo off
REM FastAPI Web Docker 启动脚本 (Windows)

setlocal enabledelayedexpansion

REM 颜色定义（Windows 10+）
set "BLUE=[94m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

REM 脚本目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"

REM 默认值
set "MODE=up"
set "DETACH=-d"
set "BUILD="
set "ENV_FILE=.env.docker"
set "COMPOSE_FILE=docker compose.yml"

REM 解析命令
if "%1"=="" (
    set "MODE=up"
) else (
    set "MODE=%1"
    shift
)

REM 解析选项
:parse_options
if "%1"=="" goto end_parse
if "%1"=="-f" (
    set "DETACH="
    shift
    goto parse_options
)
if "%1"=="--foreground" (
    set "DETACH="
    shift
    goto parse_options
)
if "%1"=="-b" (
    set "BUILD=true"
    shift
    goto parse_options
)
if "%1"=="--build" (
    set "BUILD=true"
    shift
    goto parse_options
)
if "%1"=="-h" (
    call :show_help
    exit /b 0
)
if "%1"=="--help" (
    call :show_help
    exit /b 0
)
shift
goto parse_options

:end_parse

REM 检查 Docker
call :check_docker
if errorlevel 1 exit /b 1

REM 进入项目目录
cd /d "%PROJECT_DIR%"

REM 执行命令
if "%MODE%"=="up" (
    call :start_services
) else if "%MODE%"=="down" (
    call :stop_services
) else if "%MODE%"=="restart" (
    call :restart_services
) else if "%MODE%"=="logs" (
    call :view_logs
) else if "%MODE%"=="build" (
    call :build_images
) else if "%MODE%"=="clean" (
    call :clean_resources
) else if "%MODE%"=="status" (
    call :show_status
) else if "%MODE%"=="shell" (
    call :enter_app_shell
) else if "%MODE%"=="db" (
    call :enter_db_shell
) else if "%MODE%"=="redis" (
    call :enter_redis_shell
) else if "%MODE%"=="backup" (
    call :backup_database
) else if "%MODE%"=="restore" (
    call :restore_database %1
) else (
    echo %RED%[ERROR]%NC% 未知命令: %MODE%
    echo 使用 '%0 --help' 查看帮助信息
    exit /b 1
)

exit /b 0

REM ============ 函数定义 ============

:show_help
echo.
echo %BLUE%FastAPI Web Docker 启动脚本%NC%
echo.
echo 用法: %0 [命令] [选项]
echo.
echo 命令:
echo   up              启动所有服务（默认）
echo   down            停止所有服务
echo   restart         重启所有服务
echo   logs            查看服务日志
echo   build           构建镜像
echo   clean           清理容器和卷
echo   status          查看服务状态
echo   shell           进入应用容器
echo   db              进入数据库容器
echo   redis           进入 Redis 容器
echo   backup          备份数据库
echo   restore         恢复数据库
echo.
echo 选项:
echo   -f, --foreground    前台运行（不后台运行）
echo   -b, --build         启动前重新构建镜像
echo   -h, --help          显示此帮助信息
echo.
echo 示例:
echo   %0 up                           # 启动所有服务
echo   %0 up --build                   # 重新构建并启动
echo   %0 logs                         # 查看实时日志
echo   %0 down                         # 停止所有服务
echo.
exit /b 0

:check_docker
where docker >nul 2>nul
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Docker 未安装，请先安装 Docker
    exit /b 1
)

where docker compose >nul 2>nul
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Docker Compose 未安装，请先安装 Docker Compose
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo %RED%[ERROR]%NC% Docker 守护进程未运行，请启动 Docker
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% Docker 和 Docker Compose 已安装
exit /b 0

:start_services
echo %BLUE%[INFO]%NC% 启动 FastAPI Web 服务...

if defined BUILD (
    echo %BLUE%[INFO]%NC% 重新构建镜像...
    docker compose -f "%COMPOSE_FILE%" build
)

if "%DETACH%"=="-d" (
    echo %BLUE%[INFO]%NC% 后台启动服务...
    docker compose -f "%COMPOSE_FILE%" up %DETACH%
    timeout /t 3 /nobreak
    echo %GREEN%[SUCCESS]%NC% 服务已启动
    call :show_service_info
) else (
    echo %BLUE%[INFO]%NC% 前台启动服务...
    docker compose -f "%COMPOSE_FILE%" up
)
exit /b 0

:stop_services
echo %BLUE%[INFO]%NC% 停止 FastAPI Web 服务...
docker compose -f "%COMPOSE_FILE%" down
echo %GREEN%[SUCCESS]%NC% 服务已停止
exit /b 0

:restart_services
echo %BLUE%[INFO]%NC% 重启 FastAPI Web 服务...
docker compose -f "%COMPOSE_FILE%" restart
timeout /t 2 /nobreak
echo %GREEN%[SUCCESS]%NC% 服务已重启
call :show_service_info
exit /b 0

:view_logs
echo %BLUE%[INFO]%NC% 查看服务日志...
docker compose -f "%COMPOSE_FILE%" logs -f
exit /b 0

:build_images
echo %BLUE%[INFO]%NC% 构建 Docker 镜像...
docker compose -f "%COMPOSE_FILE%" build
echo %GREEN%[SUCCESS]%NC% 镜像构建完成
exit /b 0

:clean_resources
echo %YELLOW%[WARNING]%NC% 即将删除所有容器和卷，此操作不可恢复！
set /p confirm="确认删除？(y/N): "
if /i "%confirm%"=="y" (
    echo %BLUE%[INFO]%NC% 清理资源...
    docker compose -f "%COMPOSE_FILE%" down -v
    echo %GREEN%[SUCCESS]%NC% 资源已清理
) else (
    echo %BLUE%[INFO]%NC% 已取消
)
exit /b 0

:show_status
echo %BLUE%服务状态:%NC%
docker compose -f "%COMPOSE_FILE%" ps
exit /b 0

:enter_app_shell
echo %BLUE%[INFO]%NC% 进入应用容器...
docker compose -f "%COMPOSE_FILE%" exec app bash
exit /b 0

:enter_db_shell
echo %BLUE%[INFO]%NC% 进入数据库容器...
docker compose -f "%COMPOSE_FILE%" exec mysql bash
exit /b 0

:enter_redis_shell
echo %BLUE%[INFO]%NC% 进入 Redis 容器...
docker compose -f "%COMPOSE_FILE%" exec redis sh
exit /b 0

:show_service_info
echo.
echo %GREEN%========================================%NC%
echo %GREEN%FastAPI Web 服务已启动%NC%
echo %GREEN%========================================%NC%
echo.
echo %BLUE%服务地址:%NC%
echo   FastAPI 应用: http://localhost:8080
echo   API 文档:     http://localhost:8080/docs
echo.
echo %BLUE%数据库连接:%NC%
echo   MySQL:  localhost:3307
echo   用户名: root
echo   密码:   password
echo   数据库: fastapi_web
echo.
echo %BLUE%Redis 连接:%NC%
echo   地址: localhost:6380 (密码: redispassword)
echo.
echo %BLUE%常用命令:%NC%
echo   查看日志:     %0 logs
echo   进入应用:     %0 shell
echo   进入数据库:   %0 db
echo   停止服务:     %0 down
echo.
exit /b 0

:backup_database
echo %BLUE%[INFO]%NC% 备份数据库...
if not exist "backups" mkdir backups
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
docker compose -f "%COMPOSE_FILE%" exec -T mysql mysqldump -uroot -ppassword fastapi_web > backups\mysql_backup_%mydate%_%mytime%.sql
echo %GREEN%[SUCCESS]%NC% 数据库备份完成
exit /b 0

:restore_database
if "%1"=="" (
    echo %RED%[ERROR]%NC% 请指定备份文件路径
    echo 用法: %0 restore ^<backup_file^>
    exit /b 1
)

if not exist "%1" (
    echo %RED%[ERROR]%NC% 备份文件不存在: %1
    exit /b 1
)

echo %YELLOW%[WARNING]%NC% 即将恢复数据库，此操作将覆盖现有数据！
set /p confirm="确认恢复？(y/N): "
if /i "%confirm%"=="y" (
    echo %BLUE%[INFO]%NC% 恢复数据库...
    docker compose -f "%COMPOSE_FILE%" exec -T mysql mysql -uroot -ppassword fastapi_web < "%1"
    echo %GREEN%[SUCCESS]%NC% 数据库恢复完成
) else (
    echo %BLUE%[INFO]%NC% 已取消
)
exit /b 0
