from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import json
import hmac
import hashlib
import base64
from .config import settings

# 密码加密 - 使用pbkdf2_sha256避免bcrypt问题
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=30000
)

# JWT 认证
security = HTTPBearer()

# 模拟用户数据库（实际应用中应该用真实数据库）
fake_users_db = {
    "admin": {
        "username": settings.admin_username,
        "hashed_password": settings.admin_password_hash_required,  # 强制使用哈希
        "role": "admin"
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 - 仅支持哈希密码"""
    # 如果哈希密码包含 pbkdf2 前缀，使用 hash 验证
    if hashed_password.startswith('$pbkdf2'):
        return pwd_context.verify(plain_password, hashed_password)
    # 拒绝其他格式（包括明文）
    return False

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def authenticate_user(username: str, password: str):
    """验证用户"""
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        if settings.debug:
            print(f"JWT decode error: {e}")
        raise credentials_exception

    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """获取管理员用户"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

def verify_nextauth_token_signature(token: str) -> Optional[dict]:
    """
    验证 NextAuth token 的签名并返回用户信息

    NextAuth 使用 JWS (JSON Web Signature) 格式
    """
    if not settings.nextauth_secret:
        if settings.debug:
            print("NEXTAUTH_SECRET 未配置，跳过 NextAuth token 验证")
        return None

    try:
        parts = token.split('.')
        if len(parts) != 3:
            if settings.debug:
                print(f"NextAuth token 格式错误: {len(parts)} parts")
            return None

        # 分离 header, payload, signature
        header_b64, payload_b64, signature = parts

        # 添加 padding
        def add_padding(b64: str) -> str:
            return b64 + '=' * (-len(b64) % 4)

        header_b64 = add_padding(header_b64)
        payload_b64 = add_padding(payload_b64)
        signature = add_padding(signature)

        # 解码 header 和 payload
        header_json = base64.urlsafe_b64decode(header_b64.encode()).decode()
        payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_json)

        # 验证签名
        # 重新构建签名字符串
        message = f"{header_b64}.{payload_b64}"

        # 计算期望的签名
        expected_signature = hmac.new(
            settings.nextauth_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()

        # 解码实际签名
        actual_signature = base64.urlsafe_b64decode(signature)

        # 使用恒定时间比较
        if not hmac.compare_digest(actual_signature, expected_signature):
            if settings.debug:
                print("NextAuth token 签名验证失败")
            return None

        # 检查过期时间
        if 'exp' in payload:
            exp = payload['exp']
            if exp < datetime.utcnow().timestamp():
                if settings.debug:
                    print(f"NextAuth token 已过期: {exp}")
                return None

        if settings.debug:
            print(f"NextAuth token 验证成功: {payload.get('email', 'unknown')}")

        return payload

    except Exception as e:
        if settings.debug:
            print(f"NextAuth token 验证错误: {type(e).__name__}: {e}")
        return None

async def create_token_from_nextauth(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """
    从 NextAuth token 创建 FastAPI token
    """
    # 1. 验证 NextAuth token
    nextauth_payload = verify_nextauth_token_signature(credentials.credentials)
    if not nextauth_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 NextAuth token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. 检查用户是否是 admin
    email = nextauth_payload.get('email')
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少邮箱信息",
        )

    # 检查是否在允许的 admin 邮箱列表中
    allowed_emails = [e.strip() for e in settings.nextauth_admin_emails.split(',') if e.strip()]
    if allowed_emails and email not in allowed_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )

    # 3. 生成 FastAPI token
    access_token = create_access_token(
        data={"sub": email, "role": "admin"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {"access_token": access_token, "token_type": "bearer"}
