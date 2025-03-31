from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import EmailStr
from sqlmodel import Session

from src.auth.schemas import (
    RegisterRequest, 
    LoginRequest, 
    LoginResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from src.auth.service import (
    account_register,
    account_login,
    verify_email,
    resend_verification,
    forgot_password,
    reset_password
)
from src.database import get_session

router = APIRouter(
  prefix='/user',
  tags=['users'], 
  dependencies=[],
)

# 註冊
@router.post('/register')
async def register(
  request: RegisterRequest, 
  session: Annotated[Session, Depends(get_session)]
):
  return await account_register(request, session)

# 登入
@router.post('/login', response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: Annotated[Session, Depends(get_session)]
):
    return await account_login(request, session)

# 驗證郵件
@router.get('/verify-email/{token}')
async def verify_email_route(
    token: str,
    session: Annotated[Session, Depends(get_session)]
):
    return await verify_email(token, session)

# 重新發送驗證郵件
@router.post('/resend-verification')
async def resend_verification_route(
    email: EmailStr,
    session: Annotated[Session, Depends(get_session)]
):
    return await resend_verification(email, session)

# 忘記密碼
@router.post('/forgot-password')
async def forgot_password_route(
    request: ForgotPasswordRequest,
    session: Annotated[Session, Depends(get_session)]
):
    return await forgot_password(request, session)

# 重設密碼
@router.post('/reset-password')
async def reset_password_route(
    request: ResetPasswordRequest,
    session: Annotated[Session, Depends(get_session)]
):
    return await reset_password(request, session)
