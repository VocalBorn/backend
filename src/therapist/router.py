from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from src.auth.models import User
from src.therapist.schemas import (
    TherapistProfileUpdate,
    TherapistProfileResponse,
    TherapistClientCreate,
    TherapistClientResponse,
    UserWithProfileResponse,
    TherapistRegistrationResponse,
    TherapistRegisterRequest
)
from src.therapist.services import therapist_service
from src.auth.services.permission_service import require_permission, Permission
from src.shared.database.database import get_session

router = APIRouter(prefix="/therapist", tags=["therapist"])


@router.post("/register", 
             response_model=TherapistRegistrationResponse, 
             status_code=status.HTTP_201_CREATED, 
             summary="註冊新治療師帳號",
             description="""
             提供基本資料和專業檔案來一次性註冊新的治療師帳號。
             此操作會建立使用者、治療師檔案和一個待處理的驗證申請。
             """)
async def register_therapist(
    request: TherapistRegisterRequest,
    session: Session = Depends(get_session),
):
    return await therapist_service.register_new_therapist(session=session, request=request)


@router.get(
    "/profile", 
    response_model=TherapistProfileResponse,
    summary="取得當前使用者的治療師檔案",
    description="""
    取得當前登入使用者的治療師個人檔案詳細資訊。
    此端點僅限於已擁有治療師檔案的使用者。
    """
)
async def get_my_therapist_profile(
    current_user: User = Depends(require_permission(Permission.VIEW_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    profile = therapist_service.get_therapist_profile(session, current_user.user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="治療師檔案不存在"
        )
    return profile

@router.put(
    "/profile", 
    response_model=TherapistProfileResponse,
    summary="更新當前使用者的治療師檔案",
    description="""
    更新當前登入使用者的治療師個人檔案資訊。
    此端點允許治療師修改其個人簡介、學歷、資歷、專注領域等。
    """
)
async def update_therapist_profile(
    profile_data: TherapistProfileUpdate,
    current_user: User = Depends(require_permission(Permission.MANAGE_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    profile = therapist_service.update_therapist_profile(
        session, 
        current_user.user_id, 
        profile_data
    )
    return profile

@router.delete(
    "/profile",
    summary="刪除當前使用者的治療師檔案",
    description="""
    刪除當前登入使用者的治療師個人檔案。
    此操作將永久移除治療師的個人檔案資訊。
    """
)
async def delete_therapist_profile(
    current_user: User = Depends(require_permission(Permission.MANAGE_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    success = therapist_service.delete_therapist_profile(session, current_user.user_id)
    return {"message": "治療師檔案已刪除", "success": success}

@router.get(
    "/profile/{user_id}", 
    response_model=TherapistProfileResponse,
    summary="根據用戶 ID 取得治療師檔案",
    description="""
    根據指定的用戶 ID 取得治療師的個人檔案詳細資訊。
    此端點通常用於管理員或需要查看特定治療師檔案的場景。
    """
)
async def get_therapist_profile_by_id(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.VIEW_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    profile = therapist_service.get_therapist_profile(session, user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="治療師檔案不存在"
        )
    return profile

@router.post(
    "/assign-client/{therapist_id}", 
    response_model=TherapistClientResponse,
    summary="指派客戶給治療師 (管理員功能)",
    description="""
    管理員將指定的客戶指派給指定的治療師。
    此操作會建立治療師與客戶之間的關聯。
    """
)
async def assign_client_to_therapist(
    therapist_id: UUID,
    assignment_data: TherapistClientCreate,
    current_user: User = Depends(require_permission(Permission.ASSIGN_CLIENTS)),
    session: Session = Depends(get_session)
):
    assignment = therapist_service.assign_client_to_therapist(
        session,
        therapist_id,
        assignment_data.client_id
    )
    return assignment

@router.get(
    "/my-clients", 
    response_model=List[TherapistClientResponse],
    summary="取得當前治療師的客戶列表",
    description="""
    取得當前登入治療師所指派的客戶列表。
    """
)
async def get_my_clients(
    current_user: User = Depends(require_permission(Permission.VIEW_ASSIGNED_CLIENTS)),
    session: Session = Depends(get_session)
):
    clients = therapist_service.get_therapist_clients_with_info(session, current_user.user_id)
    return clients

@router.delete(
    "/unassign-client/{client_id}",
    summary="取消客戶指派",
    description="""
    取消當前治療師與指定客戶之間的指派關係。
    """
)
async def unassign_client(
    client_id: UUID,
    current_user: User = Depends(require_permission(Permission.ASSIGN_CLIENTS)),
    session: Session = Depends(get_session)
):
    success = therapist_service.unassign_client_from_therapist(
        session,
        current_user.user_id,
        client_id
    )
    return {"message": "客戶指派已取消", "success": success}

@router.get(
    "/all", 
    response_model=List[UserWithProfileResponse],
    summary="取得所有治療師列表 (管理員功能)",
    description="""
    管理員取得所有治療師的列表，包含他們的基本用戶資訊和治療師檔案。
    """
)
async def get_all_therapists(
    current_user: User = Depends(require_permission(Permission.VIEW_ALL_USERS)),
    session: Session = Depends(get_session)
):
    therapists = therapist_service.get_all_therapists(session)
    result = []
    for therapist in therapists:
        profile = therapist_service.get_therapist_profile(session, therapist.user_id)
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