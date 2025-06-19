import datetime
import uuid
from datetime import timedelta
from typing import Optional, List
import jwt
import qrcode
import io
import base64
from sqlmodel import Session, select
from fastapi import HTTPException, status

from src.shared.database.database import engine
from src.auth.models import User, UserRole, PairingRequest, PairingRequestStatus, TherapistClient
from src.auth.services.jwt_service import SECRET_KEY


class PairingTokenService:
    """配對Token相關服務"""
    
    @staticmethod
    def generate_pairing_token(user_id: uuid.UUID, expires_minutes: int = 10) -> str:
        """生成配對token（包含用戶ID和過期時間）"""
        payload = {
            "user_id": str(user_id),
            "exp": datetime.datetime.utcnow() + timedelta(minutes=expires_minutes),
            "type": "pairing"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    @staticmethod
    def verify_pairing_token(token: str) -> Optional[uuid.UUID]:
        """驗證token並返回用戶ID"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "pairing":
                return None
            return uuid.UUID(payload["user_id"])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class QRCodeService:
    """QR Code生成服務"""
    
    @staticmethod
    def generate_qr_code(data: str) -> str:
        """生成QR Code並返回base64編碼的圖片"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()


class PairingService:
    """配對服務"""
    
    @staticmethod
    def create_pairing_request(requester_id: uuid.UUID, expires_minutes: int = 10) -> tuple[PairingRequest, str]:
        """創建配對請求並生成QR Code"""
        with Session(engine) as session:
            # 生成配對token
            token = PairingTokenService.generate_pairing_token(requester_id, expires_minutes)
            
            # 創建配對請求記錄
            pairing_request = PairingRequest(
                requester_id=requester_id,
                token=token,
                expires_at=datetime.datetime.now() + timedelta(minutes=expires_minutes)
            )
            
            session.add(pairing_request)
            session.commit()
            session.refresh(pairing_request)
            
            # 生成QR Code
            qr_code_data = QRCodeService.generate_qr_code(token)
            
            return pairing_request, qr_code_data
    
    @staticmethod
    def scan_pairing_token(token: str, scanner_id: uuid.UUID) -> PairingRequest:
        """掃描配對token並創建配對請求"""
        with Session(engine) as session:
            # 驗證token
            requester_id = PairingTokenService.verify_pairing_token(token)
            if not requester_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired pairing token"
                )
            
            # 檢查配對請求是否存在且有效
            statement = select(PairingRequest).where(
                PairingRequest.token == token,
                PairingRequest.status == PairingRequestStatus.PENDING,
                PairingRequest.expires_at > datetime.datetime.now()
            )
            pairing_request = session.exec(statement).first()
            
            if not pairing_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pairing request not found or expired"
                )
            
            # 檢查不能自己配對自己
            if pairing_request.requester_id == scanner_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot pair with yourself"
                )
            
            # 檢查用戶角色是否符合配對規則
            requester = session.get(User, pairing_request.requester_id)
            scanner = session.get(User, scanner_id)
            
            if not requester or not scanner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 驗證配對規則：治療師只能與客戶配對
            if not PairingService._is_valid_pairing(requester.role, scanner.role):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pairing: therapist can only pair with client"
                )
            
            # 檢查是否已經配對過
            if PairingService._is_already_paired(session, requester.user_id, scanner.user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Users are already paired"
                )
            
            # 更新配對請求
            pairing_request.target_id = scanner_id
            pairing_request.updated_at = datetime.datetime.now()
            
            session.add(pairing_request)
            session.commit()
            session.refresh(pairing_request)
            
            return pairing_request
    
    @staticmethod
    def respond_to_pairing_request(request_id: uuid.UUID, user_id: uuid.UUID, action: str) -> PairingRequest:
        """回應配對請求（接受或拒絕）"""
        with Session(engine) as session:
            # 查找配對請求
            pairing_request = session.get(PairingRequest, request_id)
            if not pairing_request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pairing request not found"
                )
            
            # 檢查是否為請求的接收者
            if pairing_request.requester_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to respond to this request"
                )
            
            # 檢查請求狀態
            if pairing_request.status != PairingRequestStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pairing request is not pending"
                )
            
            # 檢查是否過期
            if pairing_request.expires_at < datetime.datetime.now():
                pairing_request.status = PairingRequestStatus.EXPIRED
                session.add(pairing_request)
                session.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pairing request has expired"
                )
            
            # 處理回應
            if action == "accept":
                pairing_request.status = PairingRequestStatus.ACCEPTED
                
                # 創建治療師-客戶關係
                if pairing_request.target_id:
                    PairingService._create_therapist_client_relationship(
                        session, pairing_request.requester_id, pairing_request.target_id
                    )
                
            elif action == "reject":
                pairing_request.status = PairingRequestStatus.REJECTED
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid action. Use 'accept' or 'reject'"
                )
            
            pairing_request.updated_at = datetime.datetime.now()
            session.add(pairing_request)
            session.commit()
            session.refresh(pairing_request)
            
            return pairing_request
    
    @staticmethod
    def get_user_pairing_requests(user_id: uuid.UUID) -> dict:
        """獲取用戶的配對請求列表"""
        with Session(engine) as session:
            # 發送的配對請求
            sent_statement = select(PairingRequest).where(
                PairingRequest.requester_id == user_id
            ).order_by(PairingRequest.created_at.desc())
            sent_requests = session.exec(sent_statement).all()
            
            # 接收的配對請求
            received_statement = select(PairingRequest).where(
                PairingRequest.target_id == user_id,
                PairingRequest.status == PairingRequestStatus.PENDING
            ).order_by(PairingRequest.created_at.desc())
            received_requests = session.exec(received_statement).all()
            
            return {
                "sent_requests": sent_requests,
                "received_requests": received_requests
            }
    
    @staticmethod
    def get_user_relationships(user_id: uuid.UUID) -> dict:
        """獲取用戶的配對關係列表"""
        with Session(engine) as session:
            user = session.get(User, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if user.role == UserRole.THERAPIST:
                # 治療師查看其客戶
                statement = select(TherapistClient).where(
                    TherapistClient.therapist_id == user_id,
                    TherapistClient.is_active == True
                )
                relationships = session.exec(statement).all()
                return {"clients": relationships}
            
            elif user.role == UserRole.CLIENT:
                # 客戶查看其治療師
                statement = select(TherapistClient).where(
                    TherapistClient.client_id == user_id,
                    TherapistClient.is_active == True
                )
                relationships = session.exec(statement).all()
                return {"therapists": relationships}
            
            return {"relationships": []}
    
    @staticmethod
    def _is_valid_pairing(role1: UserRole, role2: UserRole) -> bool:
        """檢查兩個角色是否可以配對"""
        valid_pairs = [
            (UserRole.THERAPIST, UserRole.CLIENT),
            (UserRole.CLIENT, UserRole.THERAPIST)
        ]
        return (role1, role2) in valid_pairs
    
    @staticmethod
    def _is_already_paired(session: Session, user1_id: uuid.UUID, user2_id: uuid.UUID) -> bool:
        """檢查兩個用戶是否已經配對"""
        statement = select(TherapistClient).where(
            ((TherapistClient.therapist_id == user1_id) & (TherapistClient.client_id == user2_id)) |
            ((TherapistClient.therapist_id == user2_id) & (TherapistClient.client_id == user1_id)),
            TherapistClient.is_active == True
        )
        return session.exec(statement).first() is not None
    
    @staticmethod
    def _create_therapist_client_relationship(session: Session, requester_id: uuid.UUID, target_id: uuid.UUID):
        """創建治療師-客戶關係"""
        requester = session.get(User, requester_id)
        target = session.get(User, target_id)
        
        if requester.role == UserRole.THERAPIST:
            therapist_id, client_id = requester_id, target_id
        else:
            therapist_id, client_id = target_id, requester_id
        
        relationship = TherapistClient(
            therapist_id=therapist_id,
            client_id=client_id
        )
        
        session.add(relationship)