from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import EmailStr
from sqlmodel import Session

from src.auth.schemas import (
    RegisterRequest, 
    LoginRequest, 
    LoginResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateUserRequest,
    UpdatePasswordRequest,
    UserResponse
)

from src.auth.services.account_service import (
    register as account_register,
    login as account_login,
    update_password,
    update_user as account_update,
    get_user_profile,
)
from src.auth.services.email_verification_service import resend_verification, verify_email
from src.auth.services.jwt_service import verify_token
from src.auth.services.password_reset_service import forgot_password, reset_password
from src.shared.database.database import get_session

router = APIRouter(
  prefix='/user',
  tags=['users'], 
  dependencies=[],
)

@router.post(
    '/register',
    summary="用戶註冊",
    description="""
    新用戶註冊帳號。
    """
)
async def register(
  request: RegisterRequest, 
  session: Annotated[Session, Depends(get_session)]
):
  return await account_register(request, session)

@router.post(
    '/login', 
    response_model=LoginResponse,
    summary="用戶登入",
    description="""
    用戶使用電子郵件和密碼登入，成功後返回 JWT Token。
    """
)
async def login(
    request: LoginRequest,
    session: Annotated[Session, Depends(get_session)]
):
    return await account_login(request, session)

@router.get(
    '/verify-email/{token}',
    summary="驗證用戶電子郵件",
    description="""
    透過郵件中的驗證連結驗證用戶的電子郵件地址。
    """
)
async def verify_email_route(
    token: str,
    session: Annotated[Session, Depends(get_session)]
):
    return await verify_email(token, session)


@router.post(
    '/resend-verification',
    summary="重新發送驗證郵件",
    description="""
    向指定電子郵件地址重新發送帳號驗證郵件。
    """
)
async def resend_verification_route(
    email: EmailStr,
    session: Annotated[Session, Depends(get_session)]
):
    return await resend_verification(email, session)

@router.post(
    '/forgot-password',
    summary="忘記密碼",
    description="""
    用戶忘記密碼時，發送重設密碼連結到其電子郵件。
    """
)
async def forgot_password_route(
    request: ForgotPasswordRequest,
    session: Annotated[Session, Depends(get_session)]
):
    return await forgot_password(request, session)

@router.post(
    '/reset-password',
    summary="重設密碼",
    description="""
    用戶透過重設密碼連結重設其帳號密碼。
    """
)
async def reset_password_route(
    request: ResetPasswordRequest,
    session: Annotated[Session, Depends(get_session)]
):
    return await reset_password(request, session)

@router.patch(
    '/profile',
    summary="更新使用者資訊",
    description="""
    更新當前登入使用者的個人資訊，例如姓名、性別、年齡、電話等。
    """
)
async def update_profile_route(
    request: UpdateUserRequest,
    email: Annotated[str, Depends(verify_token)],
    session: Annotated[Session, Depends(get_session)]
):
    return await account_update(email, request, session)

@router.patch(
    '/password',
    summary="更新用戶密碼",
    description="""
    更新當前登入用戶的密碼。
    """
)
async def update_password_route(
    request: UpdatePasswordRequest,
    email: Annotated[str, Depends(verify_token)],
    session: Annotated[Session, Depends(get_session)]
):
    return await update_password(email, request.old_password, request.new_password, session)

@router.get(
    '/profile', 
    response_model=UserResponse,
    summary="取得當前登入用戶的資料",
    description="""
    取得當前登入用戶的詳細資料。
    """
)
async def get_profile_route(
    email: Annotated[str, Depends(verify_token)],
    session: Annotated[Session, Depends(get_session)]
):
    return await get_user_profile(email, session)
