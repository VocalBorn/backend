import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlmodel import Session, select
from pydantic import EmailStr

from src.auth.models import Account, EmailVerification
from src.utils.email_service import EmailService

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
