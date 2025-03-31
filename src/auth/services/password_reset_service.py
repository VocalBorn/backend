from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlmodel import Session, select

from src.auth.models import Account, EmailVerification
from src.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest
from src.auth.services.password_service import get_password_hash
from src.auth.services.email_verification_service import generate_verification_token
from src.utils.email_service import EmailService

async def forgot_password(request: ForgotPasswordRequest, session: Session):
    """處理忘記密碼請求"""
    # 檢查帳號是否存在
    account = session.exec(select(Account).where(Account.email == request.email)).first()
    if not account:
        # 為了安全性，即使帳號不存在也回傳相同訊息
        return {"message": "如果此電子郵件存在於系統中，您將收到重設密碼的郵件"}

    # 檢查是否有尚未過期的重設密碼請求
    active_reset = session.exec(
        select(EmailVerification)
        .where(
            EmailVerification.account_id == account.account_id,
            EmailVerification.expiry > datetime.now(),
            EmailVerification.is_used == False
        )
    ).first()

    if active_reset:
        # 如果有未過期的重設請求，讓舊的失效並建立新的
        active_reset.is_used = True
        session.add(active_reset)

    # 產生新的重設密碼 token
    reset_token = generate_verification_token()
    reset_verification = EmailVerification(
        account_id=account.account_id,
        token=reset_token,
        expiry=datetime.now() + timedelta(hours=1)  # 重設密碼連結 1 小時後過期
    )
    session.add(reset_verification)
    session.commit()

    # 發送重設密碼郵件
    email_service = EmailService()
    await email_service.send_password_reset_email(request.email, reset_token)

    return {"message": "如果此電子郵件存在於系統中，您將收到重設密碼的郵件"}

async def reset_password(request: ResetPasswordRequest, session: Session):
    """重設密碼"""
    # 檢查 token 是否有效
    verification = session.exec(
        select(EmailVerification)
        .where(
            EmailVerification.token == str(request.token),
            EmailVerification.expiry > datetime.now(),
            EmailVerification.is_used == False
        )
    ).first()

    if not verification:
        raise HTTPException(status_code=400, detail="無效或過期的重設密碼連結")

    # 更新密碼
    account = session.get(Account, verification.account_id)
    if not account:
        raise HTTPException(status_code=400, detail="找不到對應的帳號")

    # 更新密碼和標記驗證碼為已使用
    account.password = get_password_hash(request.password)
    verification.is_used = True

    session.add(account)
    session.add(verification)
    session.commit()

    return {"message": "密碼重設成功"}
