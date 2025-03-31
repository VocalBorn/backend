from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlmodel import Session, select

from src.auth.models import Account, User, EmailVerification
from src.auth.schemas import RegisterRequest, LoginRequest, LoginResponse
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
        
        # 發送驗證郵件
        await send_verification_email(request.email, verification_token)
        
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
