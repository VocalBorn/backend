import datetime
from typing import Optional
import uuid
from pydantic import BaseModel

class PairingTokenCreate(BaseModel):
    """建立配對Token的請求"""
    max_uses: Optional[int] = 1
    expires_in_hours: Optional[int] = 72  # 預設3天

class PairingTokenResponse(BaseModel):
    """配對Token回應"""
    token_id: uuid.UUID
    token_code: str
    created_at: datetime.datetime
    expires_at: datetime.datetime
    max_uses: int
    current_uses: int
    is_used: bool

class PairingTokenWithQR(PairingTokenResponse):
    """包含QR碼資料的配對Token回應"""
    qr_data: str

class TokenValidationResponse(BaseModel):
    """Token驗證回應"""
    is_valid: bool
    token_code: Optional[str] = None
    therapist_name: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None
    remaining_uses: Optional[int] = None

class PairingRequest(BaseModel):
    """配對請求"""
    token_code: str

class PairingResponse(BaseModel):
    """配對成功回應"""
    success: bool
    message: str
    therapist_id: uuid.UUID
    therapist_name: str
    paired_at: datetime.datetime

class TherapistTokenList(BaseModel):
    """治療師的Token列表"""
    tokens: list[PairingTokenResponse]
    total_count: int
