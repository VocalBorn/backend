from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from src.auth.models import User, UserRole
from src.auth.services.account_service import _create_account_and_user
from src.therapist.models import TherapistProfile, TherapistClient
from src.therapist.schemas import (
    TherapistProfileCreate, 
    TherapistProfileUpdate, 
    TherapistRegisterRequest,
    TherapistRegistrationResponse,
    TherapistProfileData
)
from src.verification.models import TherapistApplication, ApplicationStatus
from src.verification import services as verification_services

async def register_new_therapist(session: Session, request: TherapistRegisterRequest) -> TherapistRegistrationResponse:
    """Registers a new therapist in a single step, creating user, profile, and application."""
    # Check for existing license number first to fail fast
    if session.exec(select(TherapistProfile).where(TherapistProfile.license_number == request.license_number)).first():
        raise HTTPException(
            status_code=400,
            detail="License number already registered"
        )

    try:
        # 1. Create Account and User with 'CLIENT' role initially for safety
        new_user = _create_account_and_user(
            session=session,
            email=request.email,
            password=request.password,
            name=request.name,
            gender=request.gender.value,
            age=request.age,
            role=UserRole.CLIENT, # Start as client, promote upon approval
            is_verified=True  # Mark email as verified since there is no email verification step
        )

        # 2. Create a verification application
        application = TherapistApplication(
            user_id=new_user.user_id,
            status=ApplicationStatus.PENDING
        )
        session.add(application)
        session.flush()

        # 3. Create the therapist profile with all data provided
        profile = TherapistProfile(
            user_id=new_user.user_id,
            verification_application_id=application.id,
            license_number=request.license_number,
            specialization=request.specialization,
            bio=request.bio,
            years_experience=request.years_experience,
            education=request.education
        )
        session.add(profile)
        session.flush()

        session.commit()
        
        return TherapistRegistrationResponse(
            user_id=new_user.user_id,
            verification_application_id=application.id
        )
    except HTTPException as http_exc:
        session.rollback()
        raise http_exc
    except Exception as e:
        session.rollback()
        # Check if the error is from the database unique constraint on email
        if 'unique constraint' in str(e).lower() and 'accounts_email_key' in str(e).lower():
             raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register therapist: {str(e)}"
        )

def create_therapist_profile(
    session: Session, 
    user_id: UUID, 
    profile_data: TherapistProfileCreate
) -> TherapistProfile:
    user = session.exec(select(User).where(User.user_id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    if user.role != UserRole.THERAPIST:
        raise HTTPException(status_code=400, detail="只有治療師角色才能建立治療師檔案")
    
    existing_profile = get_therapist_profile(session, user_id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="該用戶已有治療師檔案")

    if profile_data.license_number:
        existing_license = session.exec(select(TherapistProfile).where(TherapistProfile.license_number == profile_data.license_number)).first()
        if existing_license:
            raise HTTPException(status_code=400, detail="執照號碼已存在")

    profile = TherapistProfile(**profile_data.model_dump(), user_id=user_id)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

def get_therapist_profile(session: Session, user_id: UUID) -> Optional[TherapistProfile]:
    return session.exec(select(TherapistProfile).where(TherapistProfile.user_id == user_id)).first()

def update_therapist_profile(
    session: Session, 
    user_id: UUID, 
    profile_data: TherapistProfileUpdate
) -> TherapistProfile:
    profile = get_therapist_profile(session, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="治療師檔案不存在")

    if profile_data.license_number:
        existing_license = session.exec(
            select(TherapistProfile).where(
                TherapistProfile.license_number == profile_data.license_number,
                TherapistProfile.user_id != user_id
            )
        ).first()
        if existing_license:
            raise HTTPException(status_code=400, detail="執照號碼已存在")

    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.now()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

def delete_therapist_profile(session: Session, user_id: UUID) -> bool:
    profile = get_therapist_profile(session, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="治療師檔案不存在")
    session.delete(profile)
    session.commit()
    return True

def assign_client_to_therapist(
    session: Session,
    therapist_id: UUID, 
    client_id: UUID,
    notes: Optional[str] = None
) -> TherapistClient:
    therapist = session.exec(select(User).where(User.user_id == therapist_id, User.role == UserRole.THERAPIST)).first()
    if not therapist:
        raise HTTPException(status_code=404, detail="治療師不存在")
    
    client = session.exec(select(User).where(User.user_id == client_id, User.role == UserRole.CLIENT)).first()
    if not client:
        raise HTTPException(status_code=404, detail="客戶不存在")
    
    existing_assignment = session.exec(select(TherapistClient).where(TherapistClient.therapist_id == therapist_id, TherapistClient.client_id == client_id, TherapistClient.is_active == True)).first()
    if existing_assignment:
        raise HTTPException(status_code=400, detail="該客戶已指派給此治療師")
    
    assignment = TherapistClient(
        therapist_id=therapist_id,
        client_id=client_id,
        assigned_date=datetime.now(),
        is_active=True,
        notes=notes,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment

def get_therapist_clients(session: Session, therapist_id: UUID) -> List[TherapistClient]:
    return session.exec(select(TherapistClient).where(TherapistClient.therapist_id == therapist_id, TherapistClient.is_active == True)).all()

def get_client_therapists(session: Session, client_id: UUID) -> List[TherapistClient]:
    return session.exec(select(TherapistClient).where(TherapistClient.client_id == client_id, TherapistClient.is_active == True)).all()

def unassign_client_from_therapist(
    session: Session, 
    therapist_id: UUID, 
    client_id: UUID
) -> bool:
    assignment = session.exec(select(TherapistClient).where(TherapistClient.therapist_id == therapist_id, TherapistClient.client_id == client_id, TherapistClient.is_active == True)).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="指派關係不存在")
    
    assignment.is_active = False
    assignment.updated_at = datetime.now()
    session.add(assignment)
    session.commit()
    return True

async def apply_to_be_therapist(
    session: Session,
    user_id: UUID, 
    application_data: TherapistProfileData
) -> TherapistProfile:
    user = session.exec(select(User).where(User.user_id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    existing_profile = get_therapist_profile(session, user_id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="該用戶已有治療師檔案")
    
    existing_license = session.exec(select(TherapistProfile).where(TherapistProfile.license_number == application_data.license_number)).first()
    if existing_license:
        raise HTTPException(status_code=400, detail="執照號碼已存在")
    
    verification_application = await verification_services.get_latest_application_for_user(user_id, session)
    if not verification_application:
        verification_application = await verification_services.create_application(user, session)

    profile = TherapistProfile(
        user_id=user_id,
        license_number=application_data.license_number,
        specialization=application_data.specialization,
        bio=application_data.bio,
        years_experience=application_data.years_experience,
        education=application_data.education,
        verification_application_id=verification_application.id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

def get_all_therapists(session: Session) -> List[User]:
    return session.exec(select(User).where(User.role == UserRole.THERAPIST)).all()
