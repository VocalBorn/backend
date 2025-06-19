from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from src.shared.database.database import engine
from src.auth.models import User
from src.auth.services.jwt_service import get_current_user
from src.auth.services.pairing_service import PairingService
from src.auth.schemas import (
    PairingQRResponse, 
    ScanPairingRequest, 
    PairingRequestResponse,
    PairingRequestsResponse,
    RespondPairingRequest,
    RelationshipsResponse,
    TherapistClientResponse
)

router = APIRouter(prefix="/pairing", tags=["pairing"])


@router.post("/generate-qr", response_model=PairingQRResponse)
async def generate_pairing_qr(
    current_user: User = Depends(get_current_user)
):
    """生成配對QR Code"""
    try:
        pairing_request, qr_code_data = PairingService.create_pairing_request(
            current_user.user_id, expires_minutes=10
        )
        
        return PairingQRResponse(
            request_id=pairing_request.request_id,
            token=pairing_request.token,
            qr_code=qr_code_data,
            expires_at=pairing_request.expires_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pairing QR code: {str(e)}"
        )


@router.post("/scan-qr", response_model=PairingRequestResponse)
async def scan_pairing_qr(
    request: ScanPairingRequest,
    current_user: User = Depends(get_current_user)
):
    """掃描QR Code並發起配對請求"""
    try:
        pairing_request = PairingService.scan_pairing_token(
            request.token, current_user.user_id
        )
        
        # 獲取用戶信息用於回應
        with Session(engine) as session:
            requester = session.get(User, pairing_request.requester_id)
            target = session.get(User, pairing_request.target_id) if pairing_request.target_id else None
            
            requester_info = {
                "name": requester.name,
                "role": requester.role.value
            } if requester else None
            
            target_info = {
                "name": target.name,
                "role": target.role.value
            } if target else None
        
        return PairingRequestResponse(
            request_id=pairing_request.request_id,
            requester_id=pairing_request.requester_id,
            target_id=pairing_request.target_id,
            status=pairing_request.status,
            expires_at=pairing_request.expires_at,
            created_at=pairing_request.created_at,
            updated_at=pairing_request.updated_at,
            requester_info=requester_info,
            target_info=target_info
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan pairing QR code: {str(e)}"
        )


@router.get("/requests", response_model=PairingRequestsResponse)
async def get_pairing_requests(
    current_user: User = Depends(get_current_user)
):
    """獲取用戶的配對請求列表"""
    try:
        requests_data = PairingService.get_user_pairing_requests(current_user.user_id)
        
        # 格式化回應數據
        sent_requests = []
        received_requests = []
        
        with Session(engine) as session:
            # 處理發送的請求
            for request in requests_data["sent_requests"]:
                requester_info = {"name": current_user.name, "role": current_user.role.value}
                target_info = None
                
                if request.target_id:
                    target = session.get(User, request.target_id)
                    if target:
                        target_info = {"name": target.name, "role": target.role.value}
                
                sent_requests.append(PairingRequestResponse(
                    request_id=request.request_id,
                    requester_id=request.requester_id,
                    target_id=request.target_id,
                    status=request.status,
                    expires_at=request.expires_at,
                    created_at=request.created_at,
                    updated_at=request.updated_at,
                    requester_info=requester_info,
                    target_info=target_info
                ))
            
            # 處理接收的請求
            for request in requests_data["received_requests"]:
                requester_info = None
                target_info = {"name": current_user.name, "role": current_user.role.value}
                
                if request.requester_id:
                    requester = session.get(User, request.requester_id)
                    if requester:
                        requester_info = {"name": requester.name, "role": requester.role.value}
                
                received_requests.append(PairingRequestResponse(
                    request_id=request.request_id,
                    requester_id=request.requester_id,
                    target_id=request.target_id,
                    status=request.status,
                    expires_at=request.expires_at,
                    created_at=request.created_at,
                    updated_at=request.updated_at,
                    requester_info=requester_info,
                    target_info=target_info
                ))
        
        return PairingRequestsResponse(
            sent_requests=sent_requests,
            received_requests=received_requests
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pairing requests: {str(e)}"
        )


@router.post("/respond/{request_id}", response_model=PairingRequestResponse)
async def respond_pairing_request(
    request_id: UUID,
    request: RespondPairingRequest,
    current_user: User = Depends(get_current_user)
):
    """回應配對請求（接受或拒絕）"""
    try:
        pairing_request = PairingService.respond_to_pairing_request(
            request_id, current_user.user_id, request.action
        )
        
        # 獲取用戶信息用於回應
        with Session(engine) as session:
            requester = session.get(User, pairing_request.requester_id)
            target = session.get(User, pairing_request.target_id) if pairing_request.target_id else None
            
            requester_info = {
                "name": requester.name,
                "role": requester.role.value
            } if requester else None
            
            target_info = {
                "name": target.name,
                "role": target.role.value
            } if target else None
        
        return PairingRequestResponse(
            request_id=pairing_request.request_id,
            requester_id=pairing_request.requester_id,
            target_id=pairing_request.target_id,
            status=pairing_request.status,
            expires_at=pairing_request.expires_at,
            created_at=pairing_request.created_at,
            updated_at=pairing_request.updated_at,
            requester_info=requester_info,
            target_info=target_info
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to respond to pairing request: {str(e)}"
        )


@router.get("/relationships", response_model=RelationshipsResponse)
async def get_relationships(
    current_user: User = Depends(get_current_user)
):
    """獲取用戶的配對關係列表"""
    try:
        relationships_data = PairingService.get_user_relationships(current_user.user_id)
        
        response_data = {}
        
        with Session(engine) as session:
            if "clients" in relationships_data:
                clients = []
                for relationship in relationships_data["clients"]:
                    client = session.get(User, relationship.client_id)
                    client_info = {
                        "name": client.name,
                        "role": client.role.value,
                        "age": client.age,
                        "gender": client.gender
                    } if client else None
                    
                    clients.append(TherapistClientResponse(
                        id=relationship.id,
                        therapist_id=relationship.therapist_id,
                        client_id=relationship.client_id,
                        created_at=relationship.paired_at,
                        client_info=client_info
                    ))
                response_data["clients"] = clients
            
            if "therapists" in relationships_data:
                therapists = []
                for relationship in relationships_data["therapists"]:
                    therapist = session.get(User, relationship.therapist_id)
                    therapist_info = {
                        "name": therapist.name,
                        "role": therapist.role.value,
                        "gender": therapist.gender
                    } if therapist else None
                    
                    therapists.append(TherapistClientResponse(
                        id=relationship.id,
                        therapist_id=relationship.therapist_id,
                        client_id=relationship.client_id,
                        created_at=relationship.paired_at,
                        therapist_info=therapist_info
                    ))
                response_data["therapists"] = therapists
        
        return RelationshipsResponse(**response_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get relationships: {str(e)}"
        )


@router.delete("/relationships/{relationship_id}")
async def remove_relationship(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """移除配對關係"""
    try:
        with Session(engine) as session:
            from src.auth.models import TherapistClient
            from sqlmodel import select
            
            # 查找關係
            statement = select(TherapistClient).where(
                TherapistClient.id == relationship_id,
                ((TherapistClient.therapist_id == current_user.user_id) | 
                 (TherapistClient.client_id == current_user.user_id)),
                TherapistClient.is_active == True
            )
            relationship = session.exec(statement).first()
            
            if not relationship:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship not found or you don't have permission"
                )
            
            # 標記為非活躍
            relationship.is_active = False
            session.add(relationship)
            session.commit()
            
            return {"message": "Relationship removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove relationship: {str(e)}"
        )