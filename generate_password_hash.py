#!/usr/bin/env python3
"""
密码哈希生成工具
用于生成 FastAPI 管理员密码的 pbkdf2_sha256 哈希值

使用方法:
    python generate_password_hash.py [密码]

如果不提供密码参数，会提示输入密码
"""

import sys
import getpass
from passlib.context import CryptContext

def generate_hash(password: str) -> str:
    """生成密码哈希"""
    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        deprecated="auto",
        pbkdf2_sha256__default_rounds=30000
    )
    return pwd_context.hash(password)

def main():
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("请输入要哈希的密码: ")

    if not password:
        print("❌ 密码不能为空")
        sys.exit(1)

    if len(password) < 8:
        print("⚠️  警告：建议使用至少 8 个字符的密码")

    hashed = generate_hash(password)

    print("\n" + "="*60)
    print("🔐 密码哈希生成成功")
    print("="*60)
    print(f"原始密码: {password}")
    print(f"哈希结果: {hashed}")
    print("="*60)
    print("\n将以下配置添加到 fastapi-web/.env 文件：")
    print(f"ADMIN_USERNAME=admin")
    print("ADMIN_PASSWORD_HASH='{}'".format(hashed))  # 注意：用单引号包围
    print(f"ADMIN_PASSWORD=")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
