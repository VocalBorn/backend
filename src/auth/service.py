import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
from sqlmodel import Session, select
from pydantic import EmailStr

from src.auth.models import Account, User, EmailVerification
from src.auth.schemas import RegisterRequest, LoginRequest, LoginResponse
from src.utils.email_service import EmailService 

# Global variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)

async def send_verification_email(email: EmailStr, token: str):
    email_service = EmailService()
    await email_service.send_verification_email(email, token)

async def verify_email(token: str, session: Session):
    verification = session.exec(
        select(EmailVerification)
        .where(
            EmailVerification.token == token,
            EmailVerification.expiry > datetime.now(),
            EmailVerification.is_used == False
        )
    ).first()
    
    if not verification:
        raise HTTPException(status_code=400, detail="無效或過期的驗證碼")
    
    account = session.get(Account, verification.account_id)
    if not account:
        raise HTTPException(status_code=400, detail="找不到對應的帳號")
    
    verification.is_used = True
    account.is_verified = True
    session.add(verification)
    session.add(account)
    session.commit()
    
    return {"message": "電子郵件驗證成功"}

async def resend_verification(email: str, session: Session):
    """ 重新發送驗證碼"""
    account = session.exec(select(Account).where(Account.email == email)).first()
    if not account or account.is_verified:
        raise HTTPException(status_code=400, detail="無效的請求")
    
    # 檢查是否有尚未過期的驗證碼
    active_verification = session.exec(
        select(EmailVerification)
        .where(
            EmailVerification.account_id == account.account_id,
            EmailVerification.expiry > datetime.now(),
            EmailVerification.is_used == False
        )
    ).first()
    
    if active_verification:
        raise HTTPException(
            status_code=400,
            detail="已有一個有效的驗證碼，請檢查您的信箱或稍後再試"
        )
    
    verification_token = generate_verification_token()
    new_verification = EmailVerification(
        account_id=account.account_id,
        token=verification_token,
        expiry=datetime.now() + timedelta(hours=24)
    )
    session.add(new_verification)
    session.commit()
    
    await send_verification_email(email, verification_token)
    return {"message": "驗證郵件已重新發送"}

async def account_register(request: RegisterRequest, session: Session) -> Account:
    existing_user = session.exec(select(Account).where(Account.email == request.email)).first()    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    try:
        # 先產生驗證碼
        verification_token = generate_verification_token()

        # 建立帳號
        new_account = Account(
            email=request.email,
            password=get_password_hash(request.password),
            is_verified=False  # 明確設置為 False
        )
        session.add(new_account)
        session.flush()  # Flush to get the account_id without committing
        
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
        session.flush()  # 確保所有資料都寫入成功
        
        # 發送驗證郵件
        await send_verification_email(request.email, verification_token)
        
        # 提交事務
        session.commit()
        session.refresh(new_user)
        return new_user

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register user: {str(e)}"
        )

async def account_login(request: LoginRequest, session: Session) -> LoginResponse:
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
