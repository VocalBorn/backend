import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlmodel import Session, select
from pydantic import EmailStr
import asyncio
import logging

from src.auth.models import Account, EmailVerification
from src.utils.email_service import EmailService

def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)

async def send_verification_email(email: EmailStr, token: str):
    """
    發送驗證郵件，包含錯誤處理和日誌記錄
    
    Args:
        email: 收件人電子郵件地址
        token: 驗證token
        
    Raises:
        HTTPException: 當郵件發送失敗且需要立即處理時
    """
    try:
        email_service = EmailService()
        await email_service.send_verification_email(email, token)
    except asyncio.TimeoutError as e:
        # 郵件發送超時
        raise HTTPException(
            status_code=500,
            detail="發送驗證郵件超時，請稍後再嘗試"
        )
    except Exception as e:
        # 其他郵件錯誤
        raise HTTPException(
            status_code=500,
            detail=f"發送驗證郵件失敗: {str(e)}"
        )

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
    """重新發送驗證郵件，包含錯誤處理"""
    
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
    
    try:
        # 使用超時處理發送郵件
        await asyncio.wait_for(
            send_verification_email(email, verification_token),
            timeout=15  # 設置超時時間為15秒
        )
        session.commit()
        return {"message": "驗證郵件已重新發送"}
    except asyncio.TimeoutError:
        # 如果超時，我們仍保存驗證記錄，但通知用戶稍後再試
        session.commit()
        return {"message": "驗證郵件發送處理中，如果您沒有收到郵件，請稍後再次請求重新發送"}
    except Exception as e:
        # 如果其他錯誤，回滾事務並通知用戶
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"重新發送驗證郵件失敗: {str(e)}"
        )
