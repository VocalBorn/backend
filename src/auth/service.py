import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from src.auth.models import Account, User
from src.auth.schemas import RegisterRequest, LoginRequest, LoginResponse

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

async def account_register(request: RegisterRequest, session: Session) -> Account:
    existing_user = session.exec(select(Account).where(Account.email == request.email)).first()    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    # Create new account and user in a transaction
    try:
        # Create new account with hashed password
        new_account = Account(email=request.email, password=get_password_hash(request.password))
        session.add(new_account)
        session.flush()  # Flush to get the account_id without committing
        
        # Create new user
        new_user = User(
            account_id=new_account.account_id,
            name=request.name,
            gender=request.gender,
            age=request.age,
        )
        session.add(new_user)
        
        # Commit the transaction
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
