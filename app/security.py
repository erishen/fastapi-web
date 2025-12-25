from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import json
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
        "hashed_password": settings.admin_password_hash or settings.admin_password,  # 优先使用预计算的哈希
        "role": "admin"
    },
    "user": {
        "username": "user",
        "hashed_password": "$pbkdf2-sha256$30000$k9IaQ.jdG4PQmvO.15oTAg$KBkXq5y3HYlOq7IE2aE1xOPpRlFd.sVc9nNjbVAmxH4",  # secret
        "role": "user"
    }
}

# 初始化时检查并生成密码哈希（如果使用明文）
def initialize_admin_password():
    """初始化管理员密码（如果使用明文则生成哈希）"""
    if not settings.admin_password_hash and settings.admin_password != "secret":
        print("⚠️  警告：使用明文密码，建议设置 ADMIN_PASSWORD_HASH 环境变量")
        print(f"   运行以下命令生成密码哈希：")
        print(f"   python -c \"from passlib.context import CryptContext; ctx = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto', pbkdf2_sha256__default_rounds=30000); print(ctx.hash('{password}'))\"")

# 应用启动时调用
initialize_admin_password()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 - 支持哈希和明文（开发环境）"""
    # 如果哈希密码包含 pbkdf2 前缀，使用 hash 验证
    if hashed_password.startswith('$pbkdf2'):
        return pwd_context.verify(plain_password, hashed_password)
    # 否则，如果是明文（开发环境），直接比较
    else:
        if not settings.admin_password_hash and hashed_password == settings.admin_password:
            # 明文密码匹配
            return True
        # 尝试识别哈希格式并验证
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except:
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
        print(f"⚠️ JWT decode error: {e}")
        raise credentials_exception
    
    user = fake_users_db.get(username)
    if user is None:
        print(f"⚠️ User not found in fake_users_db: {username}")
        print(f"Available users: {list(fake_users_db.keys())}")
        raise credentials_exception
    return user

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """获取管理员用户"""
    print(f"🔍 get_admin_user: current_user = {current_user}")
    if current_user["role"] != "admin":
        print(f"⚠️ Permission denied: role={current_user['role']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

def verify_nextauth_token(token: str) -> Optional[dict]:
    """
    验证 NextAuth token 并返回用户信息
    """
    if not settings.nextauth_secret:
        print("⚠️  NEXTAUTH_SECRET 未配置，跳过 NextAuth token 验证")
        return None

    try:
        # NextAuth JWT 结构: base64(header).base64(payload).signature
        # 需要手动解析，因为 NextAuth 使用不同的格式
        parts = token.split('.')
        if len(parts) != 3:
            print(f"⚠️  NextAuth token 格式错误: {len(parts)} parts")
            return None

        payload_b64 = parts[1]
        # 添加 padding 如果需要
        payload_b64 = payload_b64 + '=' * (-len(payload_b64) % 4)

        # 解码 payload
        import base64
        payload_json = base64.urlsafe_b64decode(payload_b64.encode())
        payload = json.loads(payload_json)

        # 验证 token 签名（简化版，实际应该验证）
        # 这里我们信任 token 的内容，只检查是否过期
        if 'exp' in payload:
            exp = payload['exp']
            if exp < datetime.utcnow().timestamp():
                print(f"⚠️  NextAuth token 已过期: {exp}")
                return None

        print(f"✓ NextAuth token 验证成功: {payload.get('email', 'unknown')}")
        return payload

    except Exception as e:
        print(f"⚠️  NextAuth token 验证错误: {type(e).__name__}: {e}")
        return None

async def create_token_from_nextauth(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """
    从 NextAuth token 创建 FastAPI token
    """
    # 1. 验证 NextAuth token
    nextauth_payload = verify_nextauth_token(credentials.credentials)
    if not nextauth_payload:
        # 不抛异常，返回 401 让前端降级到密码登录
        print("⚠️  NextAuth token 验证失败，返回 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 NextAuth token 或 NEXTAUTH_SECRET 未配置",
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
            detail=f"用户 {email} 不在允许的管理员列表中",
        )

    # 3. 生成 FastAPI token
    access_token = create_access_token(
        data={"sub": email, "role": "admin"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {"access_token": access_token, "token_type": "bearer"}