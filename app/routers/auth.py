from fastapi import APIRouter, Depends, HTTPException, status
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
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
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
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {"username": current_user["username"], "role": current_user["role"]}

@router.post("/token-from-nextauth", response_model=Token)
async def token_from_nextauth(token_data: dict = Depends(create_token_from_nextauth)):
    """
    从 NextAuth token 生成 FastAPI token

    请求头: Authorization: Bearer <nextauth_token>

    要求:
    - NEXTAUTH_SECRET 已配置
    - 用户的 email 在 NEXTAUTH_ADMIN_EMAILS 列表中
    """
    return token_data