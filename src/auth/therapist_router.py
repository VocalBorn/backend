from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.auth.models import User, UserRole
from src.auth.schemas import (
    TherapistProfileCreate,
    TherapistProfileUpdate,
    TherapistProfileResponse,
    TherapistApplicationRequest,
    TherapistClientCreate,
    TherapistClientResponse,
    UserWithProfileResponse
)
from src.auth.services.therapist_service import TherapistService
from src.auth.services.permission_service import get_current_user, require_permission, Permission
from src.shared.database.database import get_session

router = APIRouter(prefix="/therapist", tags=["therapist"])

@router.post("/apply", response_model=TherapistProfileResponse)
async def apply_to_be_therapist(
    application_data: TherapistApplicationRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """申請成為治療師"""
    therapist_service = TherapistService(session)
    profile = therapist_service.apply_to_be_therapist(
        current_user.user_id, 
        application_data
    )
    return profile

@router.get("/profile", response_model=TherapistProfileResponse)
async def get_my_therapist_profile(
    current_user: User = Depends(require_permission(Permission.VIEW_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    """取得自己的治療師檔案"""
    therapist_service = TherapistService(session)
    profile = therapist_service.get_therapist_profile(current_user.user_id)
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="治療師檔案不存在"
        )
    
    return profile

@router.post("/profile", response_model=TherapistProfileResponse)
async def create_therapist_profile(
    profile_data: TherapistProfileCreate,
    current_user: User = Depends(require_permission(Permission.MANAGE_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    """建立治療師檔案（僅限治療師角色）"""
    therapist_service = TherapistService(session)
    profile = therapist_service.create_therapist_profile(
        current_user.user_id, 
        profile_data
    )
    return profile

@router.put("/profile", response_model=TherapistProfileResponse)
async def update_therapist_profile(
    profile_data: TherapistProfileUpdate,
    current_user: User = Depends(require_permission(Permission.MANAGE_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    """更新治療師檔案"""
    therapist_service = TherapistService(session)
    profile = therapist_service.update_therapist_profile(
        current_user.user_id, 
        profile_data
    )
    return profile

@router.delete("/profile")
async def delete_therapist_profile(
    current_user: User = Depends(require_permission(Permission.MANAGE_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    """刪除治療師檔案"""
    therapist_service = TherapistService(session)
    success = therapist_service.delete_therapist_profile(current_user.user_id)
    return {"message": "治療師檔案已刪除", "success": success}

@router.get("/profile/{user_id}", response_model=TherapistProfileResponse)
async def get_therapist_profile_by_id(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.VIEW_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    """根據用戶 ID 取得治療師檔案"""
    therapist_service = TherapistService(session)
    profile = therapist_service.get_therapist_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="治療師檔案不存在"
        )
    
    return profile

@router.post("/assign-client/{therapist_id}", response_model=TherapistClientResponse)
async def assign_client_to_therapist(
    therapist_id: UUID,
    assignment_data: TherapistClientCreate,
    current_user: User = Depends(require_permission(Permission.ASSIGN_CLIENTS)),
    session: Session = Depends(get_session)
):
    """指派客戶給治療師（管理員功能）"""
    therapist_service = TherapistService(session)
    assignment = therapist_service.assign_client_to_therapist(
        therapist_id,
        assignment_data.client_id
    )
    return assignment

@router.get("/my-clients", response_model=List[TherapistClientResponse])
async def get_my_clients(
    current_user: User = Depends(require_permission(Permission.VIEW_ASSIGNED_CLIENTS)),
    session: Session = Depends(get_session)
):
    """取得我的客戶列表（治療師功能）"""
    therapist_service = TherapistService(session)
    clients = therapist_service.get_therapist_clients(current_user.user_id)
    return clients

@router.delete("/unassign-client/{client_id}")
async def unassign_client(
    client_id: UUID,
    current_user: User = Depends(require_permission(Permission.ASSIGN_CLIENTS)),
    session: Session = Depends(get_session)
):
    """取消客戶指派"""
    therapist_service = TherapistService(session)
    success = therapist_service.unassign_client_from_therapist(
        current_user.user_id,
        client_id
    )
    return {"message": "客戶指派已取消", "success": success}

@router.get("/all", response_model=List[UserWithProfileResponse])
async def get_all_therapists(
    current_user: User = Depends(require_permission(Permission.VIEW_ALL_USERS)),
    session: Session = Depends(get_session)
):
    """取得所有治療師列表（管理員功能）"""
    therapist_service = TherapistService(session)
    therapists = therapist_service.get_all_therapists()
    
    # 載入治療師檔案
    result = []
    for therapist in therapists:
        profile = therapist_service.get_therapist_profile(therapist.user_id)
        therapist_data = {
            "user_id": therapist.user_id,
            "account_id": therapist.account_id,
            "name": therapist.name,
            "gender": therapist.gender,
            "age": therapist.age,
            "phone": therapist.phone,
            "role": therapist.role,
            "created_at": therapist.created_at,
            "updated_at": therapist.updated_at,
            "therapist_profile": profile
        }
        result.append(therapist_data)
    
    return result
