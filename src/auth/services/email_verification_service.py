import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlmodel import Session, select
from pydantic import EmailStr, TypeAdapter
import logging

from src.auth.models import Account, EmailVerification
from src.utils.email_service import EmailService

def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)

async def send_verification_email(email: str, token: str):
    """
    發送驗證郵件，包含錯誤處理和日誌記錄
    
    Args:
        email: 收件人電子郵件地址
        token: 驗證token
        
    Raises:
        HTTPException: 當郵件發送失敗時
    """
    try:
        email_service = EmailService()
        email_adapter = TypeAdapter(EmailStr)
        validated_email = email_adapter.validate_python(email)
        await email_service.send_verification_email(validated_email, token)
        logging.info(f"驗證郵件已發送至 {email}")
    except Exception as e:
        logging.error(f"發送驗證郵件至 {email} 失敗: {str(e)}")
        raise

async def verify_email(token: str, session: Session):
    """
    驗證電子郵件
    
    Args:
        token: 驗證token
        session: 資料庫會話
        
    Raises:
        HTTPException: 當驗證失敗時
        
    Returns:
        dict: 包含成功訊息
    """
    verification = session.exec(
        select(EmailVerification)
        .where(
            EmailVerification.token == token,
            EmailVerification.expiry > datetime.now(),
            EmailVerification.is_used == False
        )
    ).first()
    
    if not verification:
        logging.warning(f"嘗試使用無效的驗證碼: {token}")
        raise HTTPException(status_code=400, detail="無效或過期的驗證碼")
    
    account = session.get(Account, verification.account_id)
    if not account:
        logging.error(f"找不到驗證碼對應的帳號，驗證碼ID: {verification.account_id}")
        raise HTTPException(status_code=400, detail="找不到對應的帳號")
    
    verification.is_used = True
    account.is_verified = True
    session.add(verification)
    session.add(account)
    session.commit()
    
    logging.info(f"帳號 {account.email} 驗證成功")
    return {"message": "電子郵件驗證成功"}

async def resend_verification(email: str, session: Session):
    """
    重新發送驗證郵件
    
    Args:
        email: 收件人電子郵件地址
        session: 資料庫會話
        
    Raises:
        HTTPException: 當重新發送失敗時
        
    Returns:
        dict: 包含成功訊息
    """
    account = session.exec(select(Account).where(Account.email == email)).first()
    if not account or account.is_verified:
        logging.warning(f"嘗試重新發送驗證郵件到無效的地址: {email}")
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
        logging.info(f"帳號 {email} 已有有效的驗證碼")
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
    
    try:
        await send_verification_email(email, verification_token)
        session.commit()
        logging.info(f"已重新發送驗證郵件至 {email}")
        return {"message": "驗證郵件已重新發送"}
    except Exception as e:
        session.rollback()
        logging.error(f"重新發送驗證郵件至 {email} 失敗: {str(e)}")
        # 直接傳遞 EmailService 的異常，它已經包含了適當的錯誤訊息
        raise
