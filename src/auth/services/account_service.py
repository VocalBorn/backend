from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlmodel import Session, select
from pydantic import EmailStr, TypeAdapter

from src.auth.models import Account, User, EmailVerification
from src.auth.schemas import (
    RegisterRequest, 
    LoginRequest, 
    LoginResponse, 
    UpdateUserRequest,
    UserResponse
)
from src.auth.services.jwt_service import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from src.auth.services.password_service import get_password_hash, verify_password
from src.auth.services.email_verification_service import generate_verification_token, send_verification_email

async def register(request: RegisterRequest, session: Session) -> Account:
    existing_user = session.exec(select(Account).where(Account.email == request.email)).first()    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    try:
        # 產生驗證碼
        verification_token = generate_verification_token()

        # 建立帳號
        new_account = Account(
            email=request.email,
            password=get_password_hash(request.password),
            is_verified=False
        )
        session.add(new_account)
        session.flush()
        
        # 建立使用者資料
        new_user = User(
            account_id=new_account.account_id,
            name=request.name,
            gender=request.gender,
            age=request.age,
        )
        session.add(new_user)
        
        # 建立驗證記錄
        verification = EmailVerification(
            account_id=new_account.account_id,
            token=verification_token,
            expiry=datetime.now() + timedelta(hours=24)
        )
        session.add(verification)
        session.flush()
        
        # 發送驗證郵件（已經內建重試和超時處理）
        try:
            await send_verification_email(request.email, verification_token)
        except Exception as e:
            # 即使郵件發送失敗，我們仍然創建用戶
            # 用戶可以稍後通過 resend_verification 功能重新發送驗證郵件
            pass
        
        # 提交事務並回傳用戶資料
        session.commit()
        session.refresh(new_user)
        return new_user

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register user: {str(e)}"
        )

async def login(request: LoginRequest, session: Session) -> LoginResponse:
    # 檢查使用者是否存在
    account = session.exec(
        select(Account).where(Account.email == request.email)
    ).first()
    if not account:
        raise HTTPException(
            status_code=401,
            detail="帳號或密碼錯誤"
        )
    
    # 驗證密碼
    if not verify_password(request.password, account.password):
        raise HTTPException(
            status_code=401,
            detail="帳號或密碼錯誤"
        )

    # 檢查是否已驗證
    if not account.is_verified:
        raise HTTPException(
            status_code=401,
            detail="請先驗證您的電子郵件"
        )
    
    # 產生 token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": account.email},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer"
    )

async def update_user(email: str, request: UpdateUserRequest, session: Session):
    # 檢查使用者是否存在
    account = session.exec(
        select(Account).where(Account.email == email)
    ).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail="使用者不存在"
        )

    user = session.exec(
        select(User).where(User.account_id == account.account_id)
    ).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="使用者資料不存在"
        )

    try:
        # 更新使用者資料
        if request.name is not None:
            user.name = request.name
        if request.gender is not None:
            user.gender = request.gender
        if request.age is not None:
            user.age = request.age
        if request.phone is not None:
            user.phone = request.phone

        user.updated_at = datetime.now()
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # 獲取 email
        account = session.exec(
            select(Account).where(Account.account_id == user.account_id)
        ).first()
        email = account.email if account else None

        return UserResponse(
            user_id=user.user_id,
            account_id=user.account_id,
            name=user.name,
            gender=user.gender,
            age=user.age,
            phone=user.phone,
            email=email,  # 新增 email 欄位
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"更新使用者資料失敗: {str(e)}"
        )

async def update_password(email: str, old_password: str, new_password: str, session: Session):
    # 檢查使用者是否存在
    account = session.exec(
        select(Account).where(Account.email == email)
    ).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail="使用者不存在"
        )

    # 驗證舊密碼
    if not verify_password(old_password, account.password):
        raise HTTPException(
            status_code=401,
            detail="舊密碼錯誤"
        )

    # 更新密碼
    try:
        account.password = get_password_hash(new_password)
        session.add(account)
        session.commit()
        return {"message": "密碼已更新成功"}
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"更新密碼失敗: {str(e)}"
        )

async def get_user_profile(email: str, session: Session) -> UserResponse:
    """取得用戶資料"""
    # 檢查使用者是否存在
    account = session.exec(
        select(Account).where(Account.email == email)
    ).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail="使用者不存在"
        )

    # 使用 JOIN 操作將 User 和 Account 表聯結
    user_data = session.exec(
        select(User, Account.email).join(Account, User.account_id == Account.account_id).where(Account.email == email)
    ).first()

    if not user_data:
        raise HTTPException(
            status_code=404,
            detail="使用者資料不存在"
        )

    user, account_email = user_data.User, user_data.email

    # 將資料轉換為響應格式
    return UserResponse(
        user_id=user.user_id,
        account_id=user.account_id,
        name=user.name,
        gender=user.gender,
        age=user.age,
        phone=user.phone,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        email=account_email  # 從 Account 表中獲取 email
    )
