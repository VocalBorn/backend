import random
import string
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select
from src.shared.config.config import get_settings

from src.auth.models import User, UserRole
from src.pairing.models import PairingToken
from src.pairing.schemas import (
    PairingTokenCreate, 
    PairingTokenResponse, 
    PairingTokenWithQR,
    TokenValidationResponse,
    PairingResponse,
    TherapistTokenList
)
from src.therapist.models import TherapistClient

# 避免混淆的字符集（排除0,O,1,I,l）
TOKEN_CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TOKEN_LENGTH = 8

def _generate_token_code(session: Session) -> str:
    """生成唯一的token代碼"""
    max_attempts = 100

    for _ in range(max_attempts):
        token_code = ''.join(
            random.choices(TOKEN_CHARSET, k=TOKEN_LENGTH)
        )

        # 檢查是否已存在
        existing = session.exec(
            select(PairingToken).where(PairingToken.token_code == token_code)
        ).first()

        if not existing:
            return token_code

    raise HTTPException(
        status_code=500,
        detail="無法生成唯一的token代碼"
    )

def generate_pairing_token(
    session: Session,
    therapist_id: UUID,
    token_data: PairingTokenCreate,
    base_url: str = None
) -> PairingTokenWithQR:
    """生成配對token"""

    # 驗證治療師
    therapist = session.exec(
        select(User).where(
            User.user_id == therapist_id,
            User.role == UserRole.THERAPIST
        )
    ).first()

    if not therapist:
        raise HTTPException(
            status_code=404,
            detail="治療師不存在"
        )

    # 生成token代碼
    token_code = _generate_token_code(session)

    # 計算過期時間
    expires_at = datetime.now(timezone.utc) + timedelta(hours=token_data.expires_in_hours)

    # 建立token
    token = PairingToken(
        therapist_id=therapist_id,
        token_code=token_code,
        expires_at=expires_at,
        max_uses=token_data.max_uses,
        created_at=datetime.now()
    )

    session.add(token)
    session.commit()
    session.refresh(token)

    # 取得 base_url
    if base_url is None:
        settings = get_settings()
        base_url = settings.BASE_URL or "http://localhost:8000"

    # 生成QR碼資料
    qr_data = f"{base_url}/pair/{token_code}"

    return PairingTokenWithQR(
        token_id=token.token_id,
        token_code=token.token_code,
        created_at=token.created_at,
        expires_at=token.expires_at,
        max_uses=token.max_uses,
        current_uses=token.current_uses,
        is_used=token.is_used,
        qr_data=qr_data
    )

def validate_token(session: Session, token_code: str) -> TokenValidationResponse:
    """驗證token有效性"""

    token = session.exec(
        select(PairingToken).where(PairingToken.token_code == token_code)
    ).first()

    if not token:
        return TokenValidationResponse(is_valid=False)

    # 檢查是否過期
    if datetime.now(timezone.utc) > token.expires_at:
        return TokenValidationResponse(is_valid=False)

    # 檢查使用次數
    if token.current_uses >= token.max_uses:
        return TokenValidationResponse(is_valid=False)

    # 取得治療師資訊
    therapist = session.exec(
        select(User).where(User.user_id == token.therapist_id)
    ).first()

    remaining_uses = token.max_uses - token.current_uses

    return TokenValidationResponse(
        is_valid=True,
        token_code=token.token_code,
        therapist_name=therapist.name if therapist else None,
        expires_at=token.expires_at,
        remaining_uses=remaining_uses
    )

def use_token(session: Session, token_code: str, client_id: UUID) -> PairingResponse:
    """客戶使用token進行配對"""

    # 驗證客戶
    client = session.exec(
        select(User).where(
            User.user_id == client_id,
            User.role == UserRole.CLIENT
        )
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="客戶不存在"
        )

    # 驗證token
    token = session.exec(
        select(PairingToken).where(PairingToken.token_code == token_code)
    ).first()

    if not token:
        raise HTTPException(
            status_code=404,
            detail="Token不存在"
        )

    # 檢查token是否有效
    if datetime.now(timezone.utc) > token.expires_at:
        raise HTTPException(
            status_code=400,
            detail="Token已過期"
        )

    if token.current_uses >= token.max_uses:
        raise HTTPException(
            status_code=400,
            detail="Token使用次數已達上限"
        )

    # 檢查是否已經配對
    existing_pairing = session.exec(
        select(TherapistClient).where(
            TherapistClient.therapist_id == token.therapist_id,
            TherapistClient.client_id == client_id,
            TherapistClient.is_active == True
        )
    ).first()

    if existing_pairing:
        raise HTTPException(
            status_code=400,
            detail="您已經與此治療師配對"
        )

    # 取得治療師資訊
    therapist = session.exec(
        select(User).where(User.user_id == token.therapist_id)
    ).first()

    # 建立配對關係
    pairing = TherapistClient(
        therapist_id=token.therapist_id,
        client_id=client_id,
        assigned_date=datetime.now(),
        is_active=True,
        notes=f"透過配對Token建立: {token_code}",
        pairing_source="TOKEN_PAIRING",
        pairing_token_id=token.token_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # 更新token使用狀態
    token.current_uses += 1
    if token.current_uses >= token.max_uses:
        token.is_used = True

    if not token.used_by_client_id:  # 記錄第一次使用的客戶
        token.used_by_client_id = client_id
        token.used_at = datetime.now()

    session.add(pairing)
    session.add(token)
    session.commit()

    return PairingResponse(
        success=True,
        message="配對成功",
        therapist_id=token.therapist_id,
        therapist_name=therapist.name,
        paired_at=datetime.now()
    )

def get_therapist_tokens(session: Session, therapist_id: UUID) -> TherapistTokenList:
    """取得治療師的所有token"""

    # 驗證治療師
    therapist = session.exec(
        select(User).where(
            User.user_id == therapist_id,
            User.role == UserRole.THERAPIST
        )
    ).first()

    if not therapist:
        raise HTTPException(
            status_code=404,
            detail="治療師不存在"
        )

    # 取得所有token（按建立時間倒序）
    tokens = session.exec(
        select(PairingToken)
        .where(PairingToken.therapist_id == therapist_id)
        .order_by(PairingToken.created_at.desc())
    ).all()

    token_responses = [
        PairingTokenResponse(
            token_id=token.token_id,
            token_code=token.token_code,
            created_at=token.created_at,
            expires_at=token.expires_at,
            max_uses=token.max_uses,
            current_uses=token.current_uses,
            is_used=token.is_used
        )
        for token in tokens
    ]

    return TherapistTokenList(
        tokens=token_responses,
        total_count=len(token_responses)
    )

def revoke_token(session: Session, token_id: UUID, therapist_id: UUID) -> bool:
    """撤銷token"""

    token = session.exec(
        select(PairingToken).where(
            PairingToken.token_id == token_id,
            PairingToken.therapist_id == therapist_id
        )
    ).first()

    if not token:
        raise HTTPException(
            status_code=404,
            detail="Token不存在"
        )

    # 標記為已使用（實際上是撤銷）
    token.is_used = True
    token.current_uses = token.max_uses

    session.add(token)
    session.commit()

    return True

def get_active_tokens_count(session: Session, therapist_id: UUID) -> int:
    """取得治療師目前有效的token數量"""

    count = session.exec(
        select(PairingToken).where(
            PairingToken.therapist_id == therapist_id,
            PairingToken.is_used == False,
            PairingToken.expires_at > datetime.now()
        )
    ).all()

    return len([t for t in count if t.current_uses < t.max_uses])
