import uuid
from typing import List
from fastapi import UploadFile, HTTPException, requests, status
from sqlmodel import Session, select
from datetime import timedelta

from src.shared.services.storage_service import minio_client
from src.verification.models import (
    TherapistApplication, 
    UploadedDocument,
    ApplicationStatus, 
    DocumentType
)
from src.verification.schemas import ApplicationRejectRequest

# =================================================================================================
# Constants
# =================================================================================================

VERIFICATION_BUCKET_NAME = "vocalborn-verifications"

# =================================================================================================
# Application Logic
# =================================================================================================

from src.auth.models import User, UserRole

async def create_application(current_user: User, db_session: Session) -> TherapistApplication:
    """
    Creates a new therapist verification application for a user.
    Prevents Admins and existing Therapists from creating an application.
    """
    # Block both Admins and existing Therapists from creating a new application.
    if current_user.role in (UserRole.ADMIN, UserRole.THERAPIST):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"使用者角色為 '{current_user.role.value}'，無法申請成為治療師。"
        )

    # Check if user already has a pending or approved application
    existing_application = db_session.exec(
        select(TherapistApplication).where(
            TherapistApplication.user_id == current_user.user_id,
            TherapistApplication.status.in_([ApplicationStatus.PENDING, ApplicationStatus.APPROVED])
        )
    ).first()

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="使用者已有待處理或已批准的申請。"
        )

    new_application = TherapistApplication(user_id=current_user.user_id, status=ApplicationStatus.PENDING)
    db_session.add(new_application)
    db_session.commit()
    db_session.refresh(new_application)
    return new_application

async def upload_verification_document(
    application: TherapistApplication, 
    document_type: DocumentType,
    file: UploadFile,
    db_session: Session
) -> UploadedDocument:
    """Uploads a verification document to MinIO and creates a database record."""
    
    # 1. Generate a unique object name for MinIO
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    document_id = uuid.uuid4()
    object_name = f"applications/{application.id}/{document_type.value}/{document_id}.{file_extension}"

    # 2. Ensure the bucket exists
    bucket_exists = minio_client.bucket_exists(VERIFICATION_BUCKET_NAME)
    if not bucket_exists:
        minio_client.make_bucket(VERIFICATION_BUCKET_NAME)

    # 3. Upload the file to MinIO
    try:
        minio_client.put_object(
            bucket_name=VERIFICATION_BUCKET_NAME,
            object_name=object_name,
            data=file.file,
            length=file.size,
            content_type=file.content_type
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="文件上傳超時，請稍後再試。")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="文件上傳服務暫時不可用，請檢查網路連線或稍後再試。")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件上傳失敗: {e}")

    # 4. Create the database record
    new_document = UploadedDocument(
        application_id=application.id,
        document_type=document_type,
        file_object_name=object_name
    )
    db_session.add(new_document)
    db_session.commit()
    db_session.refresh(new_document)

    # 如果申請狀態不是 APPROVED，則在文件上傳後將其重置為 PENDING
    if application.status != ApplicationStatus.APPROVED:
        application.status = ApplicationStatus.PENDING
        db_session.add(application)
        db_session.commit()
        db_session.refresh(application)
    
    return new_document

async def get_application_by_id(application_id: uuid.UUID, db_session: Session) -> TherapistApplication | None:
    """Gets a single application by its ID."""
    return db_session.get(TherapistApplication, application_id)

async def get_latest_application_for_user(user_id: uuid.UUID, db_session: Session) -> TherapistApplication | None:
    """
    Finds and returns the most recent verification application for a given user.
    This is used to allow users to resume their application process.
    """
    statement = select(TherapistApplication).where(
        TherapistApplication.user_id == user_id
    ).order_by(TherapistApplication.created_at.desc())
    
    return db_session.exec(statement).first()

async def get_document_by_id(document_id: uuid.UUID, db_session: Session) -> UploadedDocument | None:
    """Gets a single document by its ID."""
    return db_session.get(UploadedDocument, document_id)

async def get_verification_document_url(document: UploadedDocument) -> str:
    """Generates a short-lived, pre-signed URL for viewing a verification document."""
    try:
        url = minio_client.get_presigned_url(
            "GET",
            bucket_name=VERIFICATION_BUCKET_NAME,
            object_name=document.file_object_name,
            expires=timedelta(minutes=15)
        )
        return url
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate view URL: {e}")


# =================================================================================================
# Admin Logic
# =================================================================================================

async def list_applications_by_status(status: ApplicationStatus, db_session: Session) -> List[TherapistApplication]:
    """Lists all applications with a given status."""
    statement = select(TherapistApplication).where(TherapistApplication.status == status)
    return db_session.exec(statement).all()

async def list_all_applications(db_session: Session) -> List[TherapistApplication]:
    """列出所有的治療師申請，不限狀態。"""
    statement = select(TherapistApplication)
    return db_session.exec(statement).all()

async def approve_application(application: TherapistApplication, admin_user_id: uuid.UUID, db_session: Session) -> TherapistApplication:
    """Approves an application and updates the user's role to THERAPIST."""
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending applications can be approved.")
    
    # Update application status
    application.status = ApplicationStatus.APPROVED
    application.reviewed_by_id = admin_user_id
    db_session.add(application)

    # Update user's role to THERAPIST
    user = db_session.get(User, application.user_id)
    if user:
        user.role = UserRole.THERAPIST
        db_session.add(user)
    else:
        # This case should ideally not happen if foreign key constraints are in place
        # but it's good to log or handle it.
        print(f"Warning: User with ID {application.user_id} not found for application {application.id}")

    db_session.commit()
    db_session.refresh(application)
    if user: # Refresh user object if it was found and updated
        db_session.refresh(user)
    return application

async def reject_application(application: TherapistApplication, admin_user_id: uuid.UUID, rejection_data: ApplicationRejectRequest, db_session: Session) -> TherapistApplication:
    """Rejects an application."""
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending applications can be rejected.")

    application.status = ApplicationStatus.REJECTED
    application.reviewed_by_id = admin_user_id
    application.rejection_reason = rejection_data.reason
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application

async def request_action_for_application(
    application: TherapistApplication, 
    admin_user_id: uuid.UUID, 
    reason: str,
    db_session: Session
) -> TherapistApplication:
    """將申請狀態設定為 ACTION_REQUIRED，並記錄原因。"""
    if application.status not in [ApplicationStatus.PENDING, ApplicationStatus.ACTION_REQUIRED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="只有待處理或已要求補件的申請才能再次要求補件。"
        )

    application.status = ApplicationStatus.ACTION_REQUIRED
    application.reviewed_by_id = admin_user_id
    application.rejection_reason = reason # 重用 rejection_reason 欄位
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application
