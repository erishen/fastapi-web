from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..security import authenticate_user, create_access_token, get_current_user, create_token_from_nextauth
from ..config import settings
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["认证"]
)

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    role: str

@router.post("/login", response_model=Token)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录

    使用 httpOnly cookie 存储令牌，更加安全。
    同时返回 access_token 用于兼容性。
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    # 根据环境设置 secure 标志
    # 生产环境（HTTPS）设置为 True，开发环境（HTTP）设置为 False
    is_secure = settings.app_env == "production"

    # 设置 httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # 关键：httpOnly 防止 XSS 攻击
        secure=is_secure,    # 仅 HTTPS 传输（生产环境）
        samesite="lax",  # CSRF 保护
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )

    # 为了兼容性，仍然返回 token
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(response: Response):
    """
    用户登出

    清除 httpOnly cookie
    """
    is_secure = settings.app_env == "production"
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=is_secure,
        samesite="lax"
    )
    return {"message": "登出成功"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {"username": current_user["username"], "role": current_user["role"]}

@router.post("/token-from-nextauth", response_model=Token)
async def token_from_nextauth(response: Response, token_data: dict = Depends(create_token_from_nextauth)):
    """
    从 NextAuth token 生成 FastAPI token

    请求头: Authorization: Bearer <nextauth_token>

    要求:
    - NEXTAUTH_SECRET 已配置
    - 用户的 email 在 NEXTAUTH_ADMIN_EMAILS 列表中
    """
    is_secure = settings.app_env == "production"
    # 设置 httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token_data["access_token"],
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )
    return token_data