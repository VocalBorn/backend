
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session

from src.auth.models import User
from src.auth.services.permission_service import get_current_user, RequireAdmin
from src.shared.database.database import get_session
from src.verification.models import ApplicationStatus, DocumentType
from src.verification.schemas import (
    TherapistApplicationRead,
    TherapistApplicationSummary,
    ApplicationRejectRequest,
    UploadedDocumentRead
)
from src.verification import services

router = APIRouter(prefix="/verification", tags=["verification"])

# =================================================================================================
# User-facing Endpoints
# =================================================================================================



@router.get(
    "/therapist-applications/me",
    response_model=TherapistApplicationRead,
    summary="取得當前使用者的最新驗證申請"
)
async def get_my_latest_application(
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_session)
):
    """
    查詢並返回當前登入使用者的最新一筆驗證申請。
    前端可使用此端點來判斷應顯示「開始申請」按鈕，還是「繼續上傳文件」介面。
    """
    application = await services.get_latest_application_for_user(current_user.user_id, db_session)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目前使用者沒有任何驗證申請"
        )
    return application

@router.post(
    "/therapist-applications/{application_id}/documents/",
    response_model=UploadedDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="為指定的申請上傳驗證文件"
)
async def upload_document(
    application_id: uuid.UUID,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_session)
):
    """為指定的申請上傳文件（例如身分證、證書等）。"""
    application = await services.get_application_by_id(application_id, db_session)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到指定的申請")
    if application.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="使用者無權操作此申請")
    
    return await services.upload_verification_document(application, document_type, file, db_session)

# =================================================================================================
# Admin-facing Endpoints
# =================================================================================================

@router.get(
    "/admin/therapist-applications/",
    response_model=List[TherapistApplicationSummary],
    summary="列出所有待處理的治療師申請"
)
async def list_pending_applications(
    admin_user: User = Depends(RequireAdmin),
    db_session: Session = Depends(get_session)
):
    """管理員用來列出所有狀態為「待處理」的申請。"""
    return await services.list_applications_by_status(status=ApplicationStatus.PENDING, db_session=db_session)

@router.get(
    "/admin/therapist-applications/{application_id}",
    response_model=TherapistApplicationRead,
    summary="取得指定申請的詳細資訊"
)
async def get_application_details(
    application_id: uuid.UUID,
    admin_user: User = Depends(RequireAdmin),
    db_session: Session = Depends(get_session)
):
    """管理員用來取得單一申請的完整詳細資訊。"""
    application = await services.get_application_by_id(application_id=application_id, db_session=db_session)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到指定的申請")
    return application

@router.get(
    "/admin/documents/{document_id}/view",
    response_model=str,
    summary="取得安全、臨時的文件檢視 URL"
)
async def get_document_view_url(
    document_id: uuid.UUID,
    admin_user: User = Depends(RequireAdmin),
    db_session: Session = Depends(get_session)
):
    """為管理員生成並返回一個用於檢視文件的短期預簽章 URL。"""
    document = await services.get_document_by_id(document_id, db_session)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到指定的文件")
    return await services.get_verification_document_url(document)

@router.post(
    "/admin/therapist-applications/{application_id}/approve",
    response_model=TherapistApplicationRead,
    summary="批准治療師申請"
)
async def approve_application(
    application_id: uuid.UUID,
    admin_user: User = Depends(RequireAdmin),
    db_session: Session = Depends(get_session)
):
    """管理員用來批准一個待處理的申請。"""
    application = await services.get_application_by_id(application_id=application_id, db_session=db_session)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到指定的申請")
    return await services.approve_application(application=application, admin_user_id=admin_user.user_id, db_session=db_session)

@router.post(
    "/admin/therapist-applications/{application_id}/reject",
    response_model=TherapistApplicationRead,
    summary="拒絕治療師申請"
)
async def reject_application(
    application_id: uuid.UUID,
    rejection_data: ApplicationRejectRequest,
    admin_user: User = Depends(RequireAdmin),
    db_session: Session = Depends(get_session)
):
    """管理員用來拒絕一個待處理的申請。"""
    application = await services.get_application_by_id(application_id=application_id, db_session=db_session)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到指定的申請")
    return await services.reject_application(
        application=application, 
        admin_user_id=admin_user.user_id, 
        rejection_data=rejection_data,
        db_session=db_session
    )

@router.post(
    "/admin/therapist-applications/{application_id}/request-action",
    response_model=TherapistApplicationRead,
    summary="要求治療師補件",
    description="""
    管理員將指定治療師申請的狀態設定為「需補件」(ACTION_REQUIRED)，並提供補件原因。
    治療師將會收到通知，並可重新上傳所需文件。
    """
)
async def request_application_action(
    application_id: uuid.UUID,
    request_data: ApplicationRejectRequest, # 可以重用這個 Schema，或者創建一個新的
    admin_user: User = Depends(RequireAdmin),
    db_session: Session = Depends(get_session)
):
    application = await services.get_application_by_id(application_id=application_id, db_session=db_session)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到指定的申請")
    
    # 呼叫新的服務函式來處理狀態變更
    return await services.request_action_for_application(
        application=application, 
        admin_user_id=admin_user.user_id, 
        reason=request_data.reason,
        db_session=db_session
    )
