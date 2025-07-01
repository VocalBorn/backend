import uuid
from datetime import datetime
from typing import List
from sqlmodel import SQLModel
from src.verification.models import ApplicationStatus, DocumentType

# =================================================================================================
# DTOs for UploadedDocument
# =================================================================================================

class UploadedDocumentRead(SQLModel):
    """Schema for reading an uploaded document's metadata."""
    id: uuid.UUID
    document_type: DocumentType
    created_at: datetime

# =================================================================================================
# DTOs for TherapistApplication
# =================================================================================================

class TherapistApplicationRead(SQLModel):
    """Detailed view of a therapist application for admins."""
    id: uuid.UUID
    user_id: uuid.UUID
    status: ApplicationStatus
    documents: List[UploadedDocumentRead]
    rejection_reason: str | None
    reviewed_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

class TherapistApplicationSummary(SQLModel):
    """Summary view for listing multiple applications."""
    id: uuid.UUID
    user_id: uuid.UUID
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

class ApplicationRejectRequest(SQLModel):
    """Request body for rejecting an application."""
    reason: str