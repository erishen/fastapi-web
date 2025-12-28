#!/usr/bin/env python3
"""
FastAPI Web 应用安全测试脚本

用于测试安全加固功能，包括：
- IP 过滤
- 路径保护
- 速率限制
- 安全响应头
"""

import requests
import sys
import os
from typing import Dict, List

# 配置
BASE_URL = os.getenv("TEST_URL", "https://api.erishen.cn")  # 可通过环境变量修改

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def test_endpoint(path: str, method: str = "GET", expected_status: int = 200) -> bool:
    """测试单个端点"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}", timeout=10)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{path}", timeout=10)
        else:
            print_error(f"不支持的 HTTP 方法: {method}")
            return False

        if response.status_code == expected_status:
            print_success(f"{method} {path} - {response.status_code}")
            return True
        else:
            print_error(f"{method} {path} - 预期 {expected_status}, 实际 {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_error(f"{method} {path} - 请求超时（10秒）")
        return False
    except requests.exceptions.ConnectionError as e:
        print_error(f"{method} {path} - 连接错误: {e}")
        return False
    except Exception as e:
        print_error(f"{method} {path} - 错误: {e}")
        return False

def test_security_headers(path: str = "/") -> bool:
    """测试安全响应头"""
    try:
        response = requests.get(f"{BASE_URL}{path}")
        headers = response.headers

        required_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        all_ok = True
        for header, expected_value in required_headers.items():
            actual_value = headers.get(header)
            if actual_value:
                if expected_value in actual_value or actual_value == expected_value:
                    print_success(f"{header}: {actual_value}")
                else:
                    print_warning(f"{header}: {actual_value} (预期包含: {expected_value})")
            else:
                print_error(f"{header} 缺失")
                all_ok = False

        # 检查 CSP
        csp = headers.get("Content-Security-Policy")
        if csp:
            print_success(f"Content-Security-Policy: {csp[:50]}...")
        else:
            print_warning("Content-Security-Policy 缺失")

        # 检查是否移除了敏感头
        sensitive_headers = ["X-Powered-By", "Server"]
        for header in sensitive_headers:
            if header in headers:
                print_warning(f"敏感头 {header} 存在: {headers[header]}")
            else:
                print_success(f"敏感头 {header} 已移除")

        return all_ok
    except Exception as e:
        print_error(f"安全头测试失败: {e}")
        return False

def test_path_protection() -> bool:
    """测试路径保护"""
    print_info("\n=== 测试路径保护 ===")

    sensitive_paths = [
        "/.env",
        "/.git/config",
        "/sendgrid.env",
        "/app.log",
        "/config/key.pem",
        "/.DS_Store",
    ]

    all_blocked = True
    for path in sensitive_paths:
        # 这些路径应该被阻止（返回 404）
        if test_endpoint(path, expected_status=404):
            print_success(f"敏感路径已阻止: {path}")
        else:
            print_error(f"敏感路径未被阻止: {path}")
            all_blocked = False

    return all_blocked

def test_rate_limit() -> bool:
    """测试速率限制"""
    print_info("\n=== 测试速率限制 ===")

    # 发送多次请求
    rate_limit_triggered = False
    for i in range(120):  # 超过默认限制（100）
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 429:
            rate_limit_triggered = True
            print_success(f"速率限制在第 {i+1} 次请求时触发")
            print_info(f"响应头: {dict(response.headers)}")
            break

    if not rate_limit_triggered:
        print_warning("速率限制未触发（可能未配置或限制较高）")
        return False

    return True

def test_robots_txt() -> bool:
    """测试 robots.txt"""
    print_info("\n=== 测试 robots.txt ===")

    try:
        response = requests.get(f"{BASE_URL}/robots.txt")
        if response.status_code == 200:
            content = response.text
            print_success("robots.txt 访问成功")

            # 检查关键内容
            if "Disallow: /api/" in content:
                print_success("API 路径已禁止爬取")
            if "Disallow: /admin/" in content:
                print_success("Admin 路径已禁止爬取")
            if "Disallow: /docs/" in content:
                print_success("文档路径已禁止爬取")

            return True
        else:
            print_error(f"robots.txt 返回 {response.status_code}")
            return False
    except Exception as e:
        print_error(f"robots.txt 测试失败: {e}")
        return False

def test_health_check() -> bool:
    """测试健康检查"""
    print_info("\n=== 测试健康检查 ===")
    return test_endpoint("/health", expected_status=200)

def test_root_path() -> bool:
    """测试根路径"""
    print_info("\n=== 测试根路径 ===")
    return test_endpoint("/", expected_status=200)

def test_suspicious_paths() -> bool:
    """测试可疑路径"""
    print_info("\n=== 测试可疑路径 ===")

    suspicious_paths = [
        "/admin",
        "/login",
        "/wp-admin",
        "/phpmyadmin",
    ]

    # 这些路径会被记录，但默认不阻止
    for path in suspicious_paths:
        response = requests.get(f"{BASE_URL}{path}")
        if response.status_code in [404, 405]:  # 允许返回 404 或 405
            print_success(f"可疑路径处理: {path} - {response.status_code}")
        else:
            print_warning(f"可疑路径状态: {path} - {response.status_code}")

    return True

def run_all_tests():
    """运行所有测试"""
    print(f"{Colors.BOLD}{'='*50}")
    print(f"FastAPI Web 应用安全测试")
    print(f"{'='*50}{Colors.END}")
    print_info(f"测试目标: {BASE_URL}\n")

    # 先测试基本连接
    print_info("正在测试服务器连接...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print_success("服务器连接正常")
        else:
            print_warning(f"服务器响应异常: {response.status_code}")
    except Exception as e:
        print_error(f"无法连接到服务器: {e}")
        print_info(f"\n提示：")
        print_info(f"  1. 检查服务器是否运行: {BASE_URL}")
        print_info(f"  2. 使用本地测试: TEST_URL=http://localhost:8080 python test_security.py")
        print_info(f"  3. 检查防火墙和网络连接")
        return 1
    print()

    results = {
        "根路径": test_root_path(),
        "健康检查": test_health_check(),
        "安全响应头": test_security_headers(),
        "路径保护": test_path_protection(),
        "robots.txt": test_robots_txt(),
        "可疑路径": test_suspicious_paths(),
        # "速率限制": test_rate_limit(),  # 默认注释，避免触发限制
    }

    print(f"\n{Colors.BOLD}{'='*50}")
    print("测试结果汇总")
    print(f"{'='*50}{Colors.END}\n")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print(f"\n{Colors.BOLD}通过率: {passed}/{total} ({passed/total*100:.1f}%){Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 所有测试通过！{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ 部分测试失败，请检查配置{Colors.END}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_info("\n\n测试已中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n测试出错: {e}")
        sys.exit(1)
