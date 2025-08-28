# 治療師與患者預約排程系統架構規劃

## 目錄
1. [功能規劃](#功能規劃)
2. [Router 規劃](#router-規劃)
3. [Service 規劃](#service-規劃)
4. [Models 規劃](#models-規劃)
5. [架構關聯與資料流程](#架構關聯與資料流程)
6. [技術考量](#技術考量)
7. [實作優先級](#實作優先級)

---

## 功能規劃

### 1.1 完整預約流程設計

#### 標準預約流程
```
1. 患者申請預約
   ├─ 選擇治療師
   ├─ 查看可用時間段
   ├─ 選擇預約時間（需提前至少1天）
   └─ 提交預約申請

2. 系統處理申請
   ├─ 驗證時間衝突
   ├─ 檢查提前預約時間限制
   ├─ 建立預約記錄（狀態：待確認）
   └─ 發送通知給治療師

3. 治療師回應
   ├─ 接受預約（狀態：已確認）
   ├─ 拒絕預約（狀態：已拒絕）
   └─ 逾時自動取消（12小時後）

4. 預約確認後
   ├─ 系統發送確認通知
   └─ 預約進入活躍狀態
```

#### 週期性預約流程
```
1. 患者申請週期性預約
   ├─ 選擇重複模式（每週/每兩週/每月）
   ├─ 設定重複次數或結束日期
   ├─ 選擇固定時段
   └─ 提交申請

2. 系統批次建立預約
   ├─ 檢查每個時段是否衝突
   ├─ 建立主預約記錄
   ├─ 建立子預約記錄序列
   └─ 發送通知給治療師

3. 治療師回應週期性預約
   ├─ 可全部接受/拒絕
   ├─ 可個別調整特定時段
   └─ 逾時處理同標準預約
```

### 1.2 治療師可用時間管理功能

#### 可用時間設定
- **時間範圍設定**：治療師可設定每日工作時間範圍
- **特殊日期設定**：可設定假日、休假日等不可用時間
- **提前設定**：建議至少提前一週設定可用時間
- **批次操作**：支援批次設定工作日程

#### 可用時間規則
```
- 最小時間單位：1小時
- 工作時間範圍：08:00-20:00（可調整）
- 休息時間：12:00-13:00（預設午休）
- 緩衝時間：每個預約間可設定15分鐘緩衝
```

### 1.3 預約狀態生命週期

```
pending（待確認）
├─ therapist_accept → confirmed（已確認）
├─ therapist_reject → rejected（已拒絕）
├─ client_cancel → cancelled_by_client（患者取消）
├─ auto_timeout → auto_cancelled（自動取消）
└─ system_cancel → cancelled_by_system（系統取消）

confirmed（已確認）
├─ client_modify → pending_modification（待修改確認）
├─ therapist_cancel → cancelled_by_therapist（治療師取消）
├─ client_cancel → cancelled_by_client（患者取消）
├─ appointment_time → completed（已完成）
└─ no_show → no_show（未出席）

pending_modification（待修改確認）
├─ therapist_accept → confirmed（重新確認）
├─ therapist_reject → modification_rejected（修改被拒絕）
└─ auto_timeout → auto_cancelled（修改逾時取消）
```

### 1.4 自動取消機制設計

#### 自動取消觸發條件
1. **治療師逾時未回應**：12小時內未回應預約申請
2. **修改申請逾時**：修改申請12小時內治療師未回應
3. **系統維護取消**：系統檢測到資料異常

#### 背景任務設計
```python
# 使用 Celery 背景任務處理自動取消
@celery_app.task
def check_appointment_timeouts():
    """檢查並處理逾時的預約申請"""
    
    # 查找逾時的待確認預約
    timeout_appointments = find_timeout_pending_appointments()
    
    for appointment in timeout_appointments:
        # 更新狀態為自動取消
        update_appointment_status(appointment.id, "auto_cancelled")
        
        # 發送通知
        send_notification(appointment.client_id, "預約已自動取消")
        
        # 釋放時間段
        release_time_slot(appointment.therapist_id, appointment.appointment_time)
```

### 1.5 預約修改流程（重新同意機制）

#### 修改申請流程
```
1. 患者提交修改申請
   ├─ 選擇新的時間段
   ├─ 填寫修改原因
   └─ 確認修改申請

2. 系統處理修改
   ├─ 檢查新時間段衝突
   ├─ 檢查修改時限（預約前12小時）
   ├─ 建立修改記錄
   └─ 通知治療師

3. 治療師回應修改
   ├─ 同意修改（更新預約時間）
   ├─ 拒絕修改（保持原時間）
   └─ 逾時處理（取消預約）
```

---

## Router 規劃

### 2.1 患者端 API 端點

```python
# src/appointment/routers/client_appointment_router.py

@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(
    appointment_request: CreateAppointmentRequest,
    current_user: User = Depends(get_current_client)
) -> AppointmentResponse:
    """申請新預約"""

@router.post("/appointments/recurring", response_model=RecurringAppointmentResponse)
async def create_recurring_appointment(
    recurring_request: CreateRecurringAppointmentRequest,
    current_user: User = Depends(get_current_client)
) -> RecurringAppointmentResponse:
    """申請週期性預約"""

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_my_appointments(
    status: Optional[AppointmentStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_client)
) -> List[AppointmentResponse]:
    """查看我的預約列表"""

@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment_detail(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_client)
) -> AppointmentResponse:
    """查看預約詳情"""

@router.put("/appointments/{appointment_id}/modify", response_model=AppointmentResponse)
async def modify_appointment(
    appointment_id: uuid.UUID,
    modification_request: ModifyAppointmentRequest,
    current_user: User = Depends(get_current_client)
) -> AppointmentResponse:
    """修改預約時間"""

@router.delete("/appointments/{appointment_id}", response_model=MessageResponse)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    cancellation_request: CancelAppointmentRequest,
    current_user: User = Depends(get_current_client)
) -> MessageResponse:
    """取消預約"""

@router.get("/therapists/{therapist_id}/availability", response_model=List[AvailableSlot])
async def get_therapist_availability(
    therapist_id: uuid.UUID,
    date_from: datetime,
    date_to: datetime,
    current_user: User = Depends(get_current_client)
) -> List[AvailableSlot]:
    """查看治療師可用時間段"""
```

### 2.2 治療師端 API 端點

```python
# src/appointment/routers/therapist_appointment_router.py

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_therapist_appointments(
    status: Optional[AppointmentStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_therapist)
) -> List[AppointmentResponse]:
    """查看治療師的預約列表"""

@router.put("/appointments/{appointment_id}/accept", response_model=AppointmentResponse)
async def accept_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_therapist)
) -> AppointmentResponse:
    """接受預約申請"""

@router.put("/appointments/{appointment_id}/reject", response_model=AppointmentResponse)
async def reject_appointment(
    appointment_id: uuid.UUID,
    rejection_request: RejectAppointmentRequest,
    current_user: User = Depends(get_current_therapist)
) -> AppointmentResponse:
    """拒絕預約申請"""

@router.put("/appointments/{appointment_id}/modification/accept", response_model=AppointmentResponse)
async def accept_appointment_modification(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_therapist)
) -> AppointmentResponse:
    """接受預約修改申請"""

@router.put("/appointments/{appointment_id}/modification/reject", response_model=AppointmentResponse)
async def reject_appointment_modification(
    appointment_id: uuid.UUID,
    rejection_request: RejectModificationRequest,
    current_user: User = Depends(get_current_therapist)
) -> AppointmentResponse:
    """拒絕預約修改申請"""

@router.post("/availability", response_model=MessageResponse)
async def set_availability(
    availability_request: SetAvailabilityRequest,
    current_user: User = Depends(get_current_therapist)
) -> MessageResponse:
    """設定可用時間"""

@router.get("/availability", response_model=List[TherapistAvailabilityResponse])
async def get_my_availability(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_therapist)
) -> List[TherapistAvailabilityResponse]:
    """查看我的可用時間設定"""

@router.put("/availability/{availability_id}", response_model=TherapistAvailabilityResponse)
async def update_availability(
    availability_id: uuid.UUID,
    update_request: UpdateAvailabilityRequest,
    current_user: User = Depends(get_current_therapist)
) -> TherapistAvailabilityResponse:
    """更新可用時間設定"""

@router.delete("/availability/{availability_id}", response_model=MessageResponse)
async def delete_availability(
    availability_id: uuid.UUID,
    current_user: User = Depends(get_current_therapist)
) -> MessageResponse:
    """刪除可用時間設定"""
```

### 2.3 管理員 API 端點

```python
# src/appointment/routers/admin_appointment_router.py

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_all_appointments(
    status: Optional[AppointmentStatus] = None,
    therapist_id: Optional[uuid.UUID] = None,
    client_id: Optional[uuid.UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_admin)
) -> List[AppointmentResponse]:
    """管理員查看所有預約"""

@router.get("/appointments/statistics", response_model=AppointmentStatistics)
async def get_appointment_statistics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_admin)
) -> AppointmentStatistics:
    """取得預約統計資料"""

@router.put("/appointments/{appointment_id}/force-cancel", response_model=AppointmentResponse)
async def force_cancel_appointment(
    appointment_id: uuid.UUID,
    force_cancel_request: ForceCancelRequest,
    current_user: User = Depends(get_current_admin)
) -> AppointmentResponse:
    """強制取消預約"""
```

---

## Service 規劃

### 3.1 預約管理服務（函數式設計）

```python
# src/appointment/services/appointment_service.py

from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from sqlmodel import Session

async def create_appointment(
    session: Session,
    client_id: uuid.UUID,
    therapist_id: uuid.UUID,
    appointment_time: datetime,
    duration_minutes: int = 60,
    notes: Optional[str] = None
) -> Appointment:
    """建立新預約
    
    Args:
        session: 資料庫連線會話
        client_id: 患者ID
        therapist_id: 治療師ID
        appointment_time: 預約時間
        duration_minutes: 預約時長（分鐘）
        notes: 備註
        
    Returns:
        Appointment: 建立的預約物件
        
    Raises:
        ConflictError: 時間衝突時
        ValidationError: 參數驗證失敗時
        PermissionError: 權限不足時
    """

async def create_recurring_appointment(
    session: Session,
    client_id: uuid.UUID,
    therapist_id: uuid.UUID,
    start_time: datetime,
    recurrence_pattern: RecurrencePattern,
    end_date: Optional[datetime] = None,
    occurrence_count: Optional[int] = None
) -> RecurringAppointment:
    """建立週期性預約"""

async def get_appointments_by_client(
    session: Session,
    client_id: uuid.UUID,
    status_filter: Optional[AppointmentStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Appointment]:
    """取得患者的預約列表"""

async def get_appointments_by_therapist(
    session: Session,
    therapist_id: uuid.UUID,
    status_filter: Optional[AppointmentStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Appointment]:
    """取得治療師的預約列表"""

async def update_appointment_status(
    session: Session,
    appointment_id: uuid.UUID,
    new_status: AppointmentStatus,
    updated_by: uuid.UUID,
    notes: Optional[str] = None
) -> Appointment:
    """更新預約狀態"""

async def modify_appointment_time(
    session: Session,
    appointment_id: uuid.UUID,
    new_appointment_time: datetime,
    requested_by: uuid.UUID,
    modification_reason: Optional[str] = None
) -> Appointment:
    """修改預約時間"""

async def cancel_appointment(
    session: Session,
    appointment_id: uuid.UUID,
    cancelled_by: uuid.UUID,
    cancellation_reason: Optional[str] = None
) -> Appointment:
    """取消預約"""
```

### 3.2 可用時間管理服務（函數式設計）

```python
# src/appointment/services/availability_service.py

async def set_therapist_availability(
    session: Session,
    therapist_id: uuid.UUID,
    day_of_week: int,
    start_time: time,
    end_time: time,
    effective_date: Optional[date] = None,
    expiry_date: Optional[date] = None
) -> TherapistAvailability:
    """設定治療師可用時間"""

async def get_therapist_availability(
    session: Session,
    therapist_id: uuid.UUID,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[TherapistAvailability]:
    """取得治療師可用時間設定"""

async def get_available_time_slots(
    session: Session,
    therapist_id: uuid.UUID,
    date_from: datetime,
    date_to: datetime,
    duration_minutes: int = 60
) -> List[AvailableSlot]:
    """取得可預約的時間段列表"""

async def check_therapist_availability(
    session: Session,
    therapist_id: uuid.UUID,
    appointment_time: datetime,
    duration_minutes: int = 60
) -> bool:
    """檢查治療師在指定時間是否可用"""

async def block_time_slot(
    session: Session,
    therapist_id: uuid.UUID,
    blocked_date: date,
    start_time: time,
    end_time: time,
    reason: str
) -> BlockedTimeSlot:
    """封鎖特定時間段（如休假、會議等）"""
```

### 3.3 衝突檢測服務（函數式設計）

```python
# src/appointment/services/conflict_detection_service.py

async def check_time_conflict(
    session: Session,
    therapist_id: uuid.UUID,
    appointment_time: datetime,
    duration_minutes: int = 60,
    exclude_appointment_id: Optional[uuid.UUID] = None
) -> bool:
    """檢查時間衝突"""

async def check_minimum_advance_notice(
    appointment_time: datetime,
    minimum_hours: int = 24
) -> bool:
    """檢查是否符合最小提前預約時間"""

async def check_modification_deadline(
    appointment_time: datetime,
    deadline_hours: int = 12
) -> bool:
    """檢查是否在修改截止時間內"""

async def validate_appointment_business_rules(
    session: Session,
    client_id: uuid.UUID,
    therapist_id: uuid.UUID,
    appointment_time: datetime,
    duration_minutes: int = 60
) -> List[str]:
    """驗證預約業務規則，返回錯誤清單"""
```

### 3.4 自動取消任務服務（類別式設計）

```python
# src/appointment/services/auto_cancellation_service.py

class AutoCancellationService:
    """自動取消服務，負責管理預約的自動取消邏輯"""
    
    def __init__(self, session: Session, notification_service: NotificationService):
        self.session = session
        self.notification_service = notification_service
    
    async def schedule_auto_cancellation(
        self,
        appointment_id: uuid.UUID,
        timeout_hours: int = 12
    ) -> str:
        """排程自動取消任務
        
        Args:
            appointment_id: 預約ID
            timeout_hours: 逾時小時數
            
        Returns:
            str: 任務ID
        """
    
    async def cancel_auto_cancellation_task(self, task_id: str) -> bool:
        """取消自動取消任務"""
    
    async def process_timeout_appointments(self) -> List[uuid.UUID]:
        """處理逾時的預約申請"""
    
    async def handle_appointment_timeout(self, appointment_id: uuid.UUID) -> bool:
        """處理單個預約的逾時"""
```

### 3.5 通知服務（#TODO - Email實作）

```python
# src/appointment/services/notification_service.py

class NotificationService:
    """預約相關通知服務"""
    
    async def send_appointment_request_notification(
        self,
        therapist_id: uuid.UUID,
        appointment: Appointment
    ) -> bool:
        """發送預約申請通知 #TODO: 實作Email發送"""
    
    async def send_appointment_confirmation_notification(
        self,
        client_id: uuid.UUID,
        appointment: Appointment
    ) -> bool:
        """發送預約確認通知 #TODO: 實作Email發送"""
    
    async def send_appointment_cancellation_notification(
        self,
        recipient_id: uuid.UUID,
        appointment: Appointment,
        cancelled_by: str
    ) -> bool:
        """發送預約取消通知 #TODO: 實作Email發送"""
    
    async def send_modification_request_notification(
        self,
        therapist_id: uuid.UUID,
        appointment: Appointment,
        old_time: datetime,
        new_time: datetime
    ) -> bool:
        """發送預約修改申請通知 #TODO: 實作Email發送"""
```

---

## Models 規劃

### 4.1 Appointment 預約模型

```python
# src/appointment/models.py

import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
import uuid
from sqlmodel import Field, Relationship, SQLModel, Index

if TYPE_CHECKING:
    from src.auth.models import User

class AppointmentStatus(str, Enum):
    """預約狀態枚舉"""
    PENDING = "pending"                           # 待確認
    CONFIRMED = "confirmed"                       # 已確認
    REJECTED = "rejected"                         # 已拒絕
    CANCELLED_BY_CLIENT = "cancelled_by_client"   # 患者取消
    CANCELLED_BY_THERAPIST = "cancelled_by_therapist"  # 治療師取消
    CANCELLED_BY_SYSTEM = "cancelled_by_system"   # 系統取消
    AUTO_CANCELLED = "auto_cancelled"             # 自動取消
    PENDING_MODIFICATION = "pending_modification" # 待修改確認
    MODIFICATION_REJECTED = "modification_rejected"  # 修改被拒絕
    COMPLETED = "completed"                       # 已完成
    NO_SHOW = "no_show"                          # 未出席

class RecurrencePattern(str, Enum):
    """重複模式枚舉"""
    WEEKLY = "weekly"        # 每週
    BIWEEKLY = "biweekly"   # 每兩週
    MONTHLY = "monthly"      # 每月

class Appointment(SQLModel, table=True):
    """預約表"""
    __tablename__ = "appointments"
    
    appointment_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    
    # 時間相關欄位
    appointment_time: datetime.datetime = Field(nullable=False, index=True)
    duration_minutes: int = Field(default=60, nullable=False)
    end_time: datetime.datetime = Field(nullable=False, index=True)  # 計算得出的結束時間
    
    # 狀態管理
    status: AppointmentStatus = Field(default=AppointmentStatus.PENDING, nullable=False, index=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    confirmed_at: Optional[datetime.datetime] = Field(default=None)
    cancelled_at: Optional[datetime.datetime] = Field(default=None)
    
    # 備註與說明
    client_notes: Optional[str] = Field(default=None, max_length=500)
    therapist_notes: Optional[str] = Field(default=None, max_length=500)
    cancellation_reason: Optional[str] = Field(default=None, max_length=300)
    
    # 修改相關
    original_appointment_time: Optional[datetime.datetime] = Field(default=None)
    modification_reason: Optional[str] = Field(default=None, max_length=300)
    modification_requested_at: Optional[datetime.datetime] = Field(default=None)
    
    # 週期性預約關聯
    recurring_appointment_id: Optional[uuid.UUID] = Field(
        foreign_key="recurring_appointments.recurring_id", 
        default=None
    )
    sequence_number: Optional[int] = Field(default=None)  # 在週期性預約中的序號
    
    # 自動取消任務ID（用於取消背景任務）
    auto_cancel_task_id: Optional[str] = Field(default=None, max_length=100)
    
    # Relationships
    client: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Appointment.client_id]"}
    )
    therapist: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Appointment.therapist_id]"}
    )
    recurring_appointment: Optional["RecurringAppointment"] = Relationship(
        back_populates="appointments"
    )
    
    # 複合索引用於提升查詢效能
    __table_args__ = (
        Index("idx_therapist_time", "therapist_id", "appointment_time"),
        Index("idx_client_status", "client_id", "status"),
        Index("idx_status_time", "status", "appointment_time"),
    )
```

### 4.2 TherapistAvailability 治療師可用時間模型

```python
class TherapistAvailability(SQLModel, table=True):
    """治療師可用時間設定表"""
    __tablename__ = "therapist_availability"
    
    availability_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False, index=True)
    
    # 時間設定
    day_of_week: int = Field(nullable=False)  # 0=週一, 1=週二, ..., 6=週日
    start_time: datetime.time = Field(nullable=False)
    end_time: datetime.time = Field(nullable=False)
    
    # 有效期間
    effective_date: Optional[datetime.date] = Field(default=None)  # 生效日期
    expiry_date: Optional[datetime.date] = Field(default=None)     # 失效日期
    
    # 狀態
    is_active: bool = Field(default=True, nullable=False)
    
    # 備註
    notes: Optional[str] = Field(default=None, max_length=200)
    
    # 時間戳
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    therapist: "User" = Relationship()
    
    # 複合索引
    __table_args__ = (
        Index("idx_therapist_day", "therapist_id", "day_of_week"),
        Index("idx_therapist_active", "therapist_id", "is_active"),
    )
```

### 4.3 RecurringAppointment 週期性預約模型

```python
class RecurringAppointment(SQLModel, table=True):
    """週期性預約主表"""
    __tablename__ = "recurring_appointments"
    
    recurring_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    
    # 重複設定
    recurrence_pattern: RecurrencePattern = Field(nullable=False)
    start_date: datetime.date = Field(nullable=False)
    end_date: Optional[datetime.date] = Field(default=None)
    occurrence_count: Optional[int] = Field(default=None)  # 重複次數
    
    # 時間設定
    appointment_time: datetime.time = Field(nullable=False)  # 固定時間
    duration_minutes: int = Field(default=60, nullable=False)
    
    # 狀態
    is_active: bool = Field(default=True, nullable=False)
    total_generated: int = Field(default=0, nullable=False)  # 已生成的預約數
    
    # 備註
    notes: Optional[str] = Field(default=None, max_length=500)
    
    # 時間戳
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    client: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[RecurringAppointment.client_id]"}
    )
    therapist: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[RecurringAppointment.therapist_id]"}
    )
    appointments: List[Appointment] = Relationship(back_populates="recurring_appointment")
    
    # 索引
    __table_args__ = (
        Index("idx_recurring_therapist", "therapist_id", "is_active"),
        Index("idx_recurring_client", "client_id", "is_active"),
    )
```

### 4.4 BlockedTimeSlot 封鎖時間段模型

```python
class BlockedTimeSlot(SQLModel, table=True):
    """治療師封鎖時間段表（休假、會議等）"""
    __tablename__ = "blocked_time_slots"
    
    blocked_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    therapist_id: uuid.UUID = Field(foreign_key="users.user_id", nullable=False, index=True)
    
    # 時間設定
    blocked_date: datetime.date = Field(nullable=False, index=True)
    start_time: datetime.time = Field(nullable=False)
    end_time: datetime.time = Field(nullable=False)
    
    # 說明
    reason: str = Field(nullable=False, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=300)
    
    # 狀態
    is_active: bool = Field(default=True, nullable=False)
    
    # 時間戳
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    therapist: "User" = Relationship()
    
    # 複合索引
    __table_args__ = (
        Index("idx_therapist_date", "therapist_id", "blocked_date"),
    )
```

### 4.5 AppointmentHistory 預約歷史記錄模型

```python
class AppointmentHistory(SQLModel, table=True):
    """預約狀態變更歷史記錄表"""
    __tablename__ = "appointment_history"
    
    history_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    appointment_id: uuid.UUID = Field(foreign_key="appointments.appointment_id", nullable=False, index=True)
    
    # 變更資訊
    previous_status: Optional[AppointmentStatus] = Field(default=None)
    new_status: AppointmentStatus = Field(nullable=False)
    changed_by: uuid.UUID = Field(foreign_key="users.user_id", nullable=False)
    
    # 時間變更（如有）
    previous_appointment_time: Optional[datetime.datetime] = Field(default=None)
    new_appointment_time: Optional[datetime.datetime] = Field(default=None)
    
    # 變更原因與備註
    change_reason: Optional[str] = Field(default=None, max_length=300)
    notes: Optional[str] = Field(default=None, max_length=500)
    
    # 時間戳
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, nullable=False)
    
    # Relationships
    appointment: Appointment = Relationship()
    changed_by_user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[AppointmentHistory.changed_by]"}
    )
```

---

## 架構關聯與資料流程

### 5.1 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  患者端API          │  治療師端API        │  管理員API          │
│  - 申請預約          │  - 管理可用時間      │  - 預約統計          │
│  - 查看預約          │  - 回應預約申請      │  - 強制取消          │
│  - 修改預約          │  - 查看預約列表      │  - 系統監控          │
│  - 取消預約          │  - 處理修改申請      │                     │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  預約管理服務        │  可用時間管理服務    │  衝突檢測服務        │
│  - create_appointment │  - set_availability │  - check_conflict   │
│  - modify_appointment │  - get_available_slots│ - validate_rules   │
│  - cancel_appointment │  - block_time_slot   │  - check_deadlines  │
├─────────────────────────────────────────────────────────────────┤
│  自動取消服務        │  通知服務            │  統計報告服務        │
│  - schedule_cancellation│ - send_notifications │ - generate_stats   │
│  - process_timeouts   │  - email_service (#TODO)│ - export_reports  │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  Appointment         │  TherapistAvailability│  RecurringAppointment│
│  - 預約核心資料       │  - 可用時間設定       │  - 週期性預約設定     │
│                     │                      │                     │
│  BlockedTimeSlot    │  AppointmentHistory   │  Background Tasks   │
│  - 封鎖時間段        │  - 狀態變更歷史       │  - Celery Tasks     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 預約申請到確認的完整流程

```
患者申請預約流程：
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐
│ 選擇治療師 │ -> │ 選擇時間段 │ -> │ 提交申請   │ -> │ 系統驗證 │
└─────────┘    └──────────┘    └──────────┘    └─────────┘
                                                     │
                                                     ▼
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐
│ 發送通知 │ <- │ 建立預約   │ <- │ 排程自動取消│ <- │ 驗證通過 │
└─────────┘    └──────────┘    └──────────┘    └─────────┘
     │
     ▼
┌──────────────────────────────┐
│        治療師回應              │
├──────────────────────────────┤
│ ┌─────┐  ┌─────┐  ┌─────────┐│
│ │接受  │  │拒絕  │  │逾時自動  ││
│ │預約  │  │預約  │  │取消     ││
│ └─────┘  └─────┘  └─────────┘│
└──────────────────────────────┘
     │         │         │
     ▼         ▼         ▼
┌─────────┐┌─────────┐┌─────────┐
│預約確認  ││預約拒絕  ││自動取消  │
│發送通知  ││發送通知  ││發送通知  │
└─────────┘└─────────┘└─────────┘
```

### 5.3 修改預約的重新同意流程

```
預約修改流程：
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐
│患者發起修改│ -> │檢查修改期限│ -> │驗證新時間  │ -> │建立修改申請│
└─────────┘    └──────────┘    └──────────┘    └─────────┘
                     │               │               │
                     ▼               ▼               ▼
                ┌─────────┐    ┌─────────┐    ┌─────────┐
                │超過期限  │    │時間衝突  │    │通知治療師│
                │拒絕修改  │    │拒絕修改  │    │等待回應  │
                └─────────┘    └─────────┘    └─────────┘
                                                    │
                                                    ▼
                            ┌──────────────────────────────┐
                            │        治療師回應修改申請      │
                            ├──────────────────────────────┤
                            │ ┌─────┐  ┌─────┐  ┌─────────┐│
                            │ │同意  │  │拒絕  │  │逾時自動  ││
                            │ │修改  │  │修改  │  │取消     ││
                            │ └─────┘  └─────┘  └─────────┘│
                            └──────────────────────────────┘
                                 │         │         │
                                 ▼         ▼         ▼
                            ┌─────────┐┌─────────┐┌─────────┐
                            │更新預約時間││保持原時間││取消整個預約│
                            │狀態:已確認││狀態:已確認││狀態:已取消 │
                            │發送確認通知││發送拒絕通知││發送取消通知│
                            └─────────┘└─────────┘└─────────┘
```

### 5.4 自動取消的背景任務流程

```
自動取消背景任務流程：

預約建立時：
┌─────────┐    ┌──────────────┐    ┌─────────────┐
│建立預約記錄│ -> │排程Celery任務 │ -> │設定12小時後執行│
└─────────┘    └──────────────┘    └─────────────┘
     │               │                     │
     ▼               ▼                     ▼
┌─────────┐    ┌──────────────┐    ┌─────────────┐
│狀態:待確認│    │存儲任務ID    │    │等待治療師回應 │
└─────────┘    └──────────────┘    └─────────────┘

治療師回應時：
┌─────────┐    ┌──────────────┐    ┌─────────────┐
│治療師接受 │ -> │取消自動取消任務│ -> │預約狀態:已確認│
│或拒絕預約 │    │                │    │              │
└─────────┘    └──────────────┘    └─────────────┘

自動取消執行時：
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│12小時後任務執行│ -> │檢查預約狀態   │ -> │仍為待確認？   │
└─────────────┘    └──────────────┘    └─────────────┘
                                           │
                                           ▼
                    ┌─────────────┐    ┌─────────────┐
                    │更新為自動取消 │ <- │是，自動取消   │
                    │發送通知給雙方 │    │              │
                    └─────────────┘    └─────────────┘
```

### 5.5 週期性預約的處理流程

```
週期性預約處理流程：

申請階段：
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│患者申請週期性 │ -> │設定重複模式   │ -> │計算所有時間點 │
│預約          │    │(每週/雙週/月) │    │              │
└─────────────┘    └──────────────┘    └─────────────┘
     │
     ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│批次檢查衝突  │ -> │建立主預約記錄 │ -> │建立子預約序列 │
└─────────────┘    └──────────────┘    └─────────────┘
     │
     ▼
┌─────────────┐    ┌──────────────┐
│通知治療師    │ -> │等待回應       │
└─────────────┘    └──────────────┘

治療師回應：
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│全部接受      │ -> │所有子預約確認 │ -> │開始排程      │
└─────────────┘    └──────────────┘    └─────────────┘

┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│全部拒絕      │ -> │所有子預約拒絕 │ -> │通知患者      │
└─────────────┘    └──────────────┘    └─────────────┘

┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│部分調整      │ -> │個別處理子預約 │ -> │混合狀態管理   │
└─────────────┘    └──────────────┘    └─────────────┘
```

---

## 技術考量

### 6.1 時區處理

```python
# 建議的時區處理策略

import pytz
from datetime import datetime
from zoneinfo import ZoneInfo

# 系統統一使用 UTC 儲存時間
def convert_to_utc(local_time: datetime, timezone_str: str = "Asia/Taipei") -> datetime:
    """將本地時間轉換為UTC時間"""
    if local_time.tzinfo is None:
        # 假設是台灣時間
        tz = ZoneInfo(timezone_str)
        local_time = local_time.replace(tzinfo=tz)
    
    return local_time.astimezone(ZoneInfo("UTC"))

def convert_to_local(utc_time: datetime, timezone_str: str = "Asia/Taipei") -> datetime:
    """將UTC時間轉換為本地時間"""
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=ZoneInfo("UTC"))
    
    return utc_time.astimezone(ZoneInfo(timezone_str))

# 在模型中的應用
class Appointment(SQLModel, table=True):
    # 統一使用 UTC 時間儲存
    appointment_time: datetime.datetime = Field(nullable=False)
    
    def get_local_time(self, timezone_str: str = "Asia/Taipei") -> datetime:
        """取得本地時間顯示"""
        return convert_to_local(self.appointment_time, timezone_str)
```

### 6.2 背景任務處理（自動取消）

```python
# 使用 Celery 處理自動取消任務

from celery import Celery
from datetime import datetime, timedelta

@celery_app.task(bind=True, max_retries=3)
def auto_cancel_appointment_task(self, appointment_id: str, scheduled_time: str):
    """自動取消預約的背景任務"""
    try:
        # 檢查預約是否仍需要取消
        with get_session() as session:
            appointment = get_appointment_by_id(session, uuid.UUID(appointment_id))
            
            if not appointment:
                return f"預約 {appointment_id} 不存在"
            
            if appointment.status != AppointmentStatus.PENDING:
                return f"預約 {appointment_id} 狀態已改變，無需自動取消"
            
            # 執行自動取消
            result = await handle_appointment_timeout(session, appointment)
            return f"預約 {appointment_id} 已自動取消: {result}"
            
    except Exception as exc:
        # 重試機制
        raise self.retry(exc=exc, countdown=60)

# 排程自動取消任務
def schedule_auto_cancellation(appointment_id: uuid.UUID, timeout_hours: int = 12) -> str:
    """排程自動取消任務"""
    eta = datetime.utcnow() + timedelta(hours=timeout_hours)
    
    result = auto_cancel_appointment_task.apply_async(
        args=[str(appointment_id), eta.isoformat()],
        eta=eta
    )
    
    return result.id

# 取消自動取消任務
def cancel_auto_cancellation(task_id: str) -> bool:
    """取消自動取消任務"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return True
    except Exception:
        return False
```

### 6.3 資料庫索引優化

```python
# 針對常用查詢進行索引優化

# 1. 治療師時間查詢索引
# CREATE INDEX idx_therapist_time ON appointments (therapist_id, appointment_time);

# 2. 患者預約狀態查詢索引
# CREATE INDEX idx_client_status ON appointments (client_id, status);

# 3. 時間範圍查詢索引
# CREATE INDEX idx_appointment_time_range ON appointments (appointment_time, status);

# 4. 可用時間查詢索引
# CREATE INDEX idx_availability_therapist_day ON therapist_availability (therapist_id, day_of_week, is_active);

# 5. 複合查詢索引（治療師 + 時間 + 狀態）
# CREATE INDEX idx_complex_query ON appointments (therapist_id, appointment_time, status);

# 在模型中定義複合索引
class Appointment(SQLModel, table=True):
    # ... 其他欄位 ...
    
    __table_args__ = (
        Index("idx_therapist_time", "therapist_id", "appointment_time"),
        Index("idx_client_status", "client_id", "status"),
        Index("idx_status_time", "status", "appointment_time"),
        # 支援時間範圍查詢的部分索引
        Index("idx_future_appointments", "therapist_id", "appointment_time", 
              postgresql_where=text("appointment_time >= NOW()")),
    )
```

### 6.4 併發衝突處理

```python
# 使用資料庫層級鎖定處理併發問題

from sqlmodel import select
from sqlalchemy import and_

async def create_appointment_with_lock(
    session: Session,
    client_id: uuid.UUID,
    therapist_id: uuid.UUID,
    appointment_time: datetime,
    duration_minutes: int = 60
) -> Appointment:
    """使用鎖定機制建立預約，避免併發衝突"""
    
    end_time = appointment_time + timedelta(minutes=duration_minutes)
    
    # 使用 SELECT FOR UPDATE 鎖定相關記錄
    existing_appointments = session.exec(
        select(Appointment)
        .where(
            and_(
                Appointment.therapist_id == therapist_id,
                Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
                # 檢查時間重疊
                and_(
                    Appointment.appointment_time < end_time,
                    Appointment.end_time > appointment_time
                )
            )
        )
        .with_for_update()  # 鎖定查詢結果
    ).all()
    
    if existing_appointments:
        raise ConflictError("選定的時間段已有其他預約")
    
    # 建立新預約
    new_appointment = Appointment(
        client_id=client_id,
        therapist_id=therapist_id,
        appointment_time=appointment_time,
        end_time=end_time,
        duration_minutes=duration_minutes
    )
    
    session.add(new_appointment)
    session.commit()
    session.refresh(new_appointment)
    
    return new_appointment

# 使用樂觀鎖定處理更新衝突
class Appointment(SQLModel, table=True):
    # ... 其他欄位 ...
    
    version: int = Field(default=1, nullable=False)  # 版本號用於樂觀鎖定
    
    def update_with_version_check(self, session: Session, **kwargs) -> bool:
        """使用版本檢查進行更新"""
        current_version = self.version
        
        # 更新資料
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        self.version += 1
        self.updated_at = datetime.now()
        
        # 執行更新，檢查版本號
        result = session.exec(
            update(Appointment)
            .where(
                and_(
                    Appointment.appointment_id == self.appointment_id,
                    Appointment.version == current_version
                )
            )
            .values(**kwargs, version=self.version, updated_at=self.updated_at)
        )
        
        return result.rowcount > 0
```

### 6.5 API限流和安全性

```python
# 使用 slowapi 進行 API 限流

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# 在路由中應用限流
@router.post("/appointments")
@limiter.limit("10/minute")  # 每分鐘最多10次預約申請
async def create_appointment(
    request: Request,
    appointment_request: CreateAppointmentRequest,
    current_user: User = Depends(get_current_client)
):
    """建立預約（帶限流保護）"""
    pass

# 安全性驗證
async def verify_appointment_permission(
    appointment_id: uuid.UUID,
    current_user: User,
    session: Session
) -> Appointment:
    """驗證使用者對預約的操作權限"""
    
    appointment = session.get(Appointment, appointment_id)
    
    if not appointment:
        raise HTTPException(status_code=404, detail="預約不存在")
    
    # 檢查權限
    if current_user.role == UserRole.ADMIN:
        return appointment
    elif current_user.role == UserRole.CLIENT:
        if appointment.client_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="無權限訪問此預約")
    elif current_user.role == UserRole.THERAPIST:
        if appointment.therapist_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="無權限訪問此預約")
    else:
        raise HTTPException(status_code=403, detail="權限不足")
    
    return appointment

# 輸入驗證和清理
from pydantic import validator

class CreateAppointmentRequest(BaseModel):
    therapist_id: uuid.UUID
    appointment_time: datetime
    duration_minutes: int = 60
    notes: Optional[str] = None
    
    @validator('appointment_time')
    def validate_appointment_time(cls, v):
        """驗證預約時間"""
        # 檢查是否為未來時間
        if v <= datetime.now():
            raise ValueError('預約時間必須是未來時間')
        
        # 檢查是否為整點
        if v.minute != 0 or v.second != 0:
            raise ValueError('預約時間必須為整點')
        
        return v
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        """驗證預約時長"""
        if v not in [30, 60, 90, 120]:
            raise ValueError('預約時長必須為30、60、90或120分鐘')
        
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        """清理和驗證備註"""
        if v is not None:
            # 移除前後空白
            v = v.strip()
            # 檢查長度
            if len(v) > 500:
                raise ValueError('備註不能超過500個字元')
            # 基本的安全清理（移除HTML標籤等）
            # 這裡可以使用更完整的清理函數
        
        return v
```

---

## 實作優先級

### Phase 1: 核心預約功能 (優先級: 高)
1. **基礎模型建立**
   - Appointment 模型
   - TherapistAvailability 模型
   - 基礎資料庫遷移

2. **基本預約流程**
   - 患者申請預約 API
   - 治療師回應預約 API
   - 預約狀態管理

3. **可用時間管理**
   - 治療師設定可用時間 API
   - 查詢可用時間段 API

### Phase 2: 業務規則實作 (優先級: 高)
1. **時間衝突檢測**
   - 實作 conflict_detection_service
   - 提前預約時間驗證
   - 修改截止時間驗證

2. **自動取消機制**
   - Celery 背景任務設定
   - 自動取消邏輯實作
   - 任務排程和取消

### Phase 3: 進階功能 (優先級: 中)
1. **預約修改功能**
   - 修改申請流程
   - 重新同意機制
   - 修改歷史記錄

2. **週期性預約**
   - RecurringAppointment 模型
   - 週期性預約建立邏輯
   - 批次管理功能

### Phase 4: 系統優化 (優先級: 中)
1. **效能優化**
   - 資料庫索引優化
   - 查詢效能調優
   - 快取策略實作

2. **併發處理**
   - 資料庫鎖定機制
   - 樂觀鎖定實作
   - 衝突解決策略

### Phase 5: 管理和監控 (優先級: 低)
1. **管理員功能**
   - 預約統計 API
   - 強制取消功能
   - 系統監控介面

2. **通知系統**
   - Email 通知實作 (#TODO)
   - 通知模板設計
   - 通知狀態追蹤

### Phase 6: 安全性和穩定性 (優先級: 低)
1. **安全性強化**
   - API 限流實作
   - 輸入驗證加強
   - 權限控制細化

2. **錯誤處理和日誌**
   - 完整的錯誤處理機制
   - 系統日誌記錄
   - 監控告警設定

---

## 結語

本架構規劃文件提供了完整的治療師與患者預約排程系統設計方案。架構設計遵循了專案的技術規範和最佳實踐，包括：

- **模組化設計**：清楚分離 Router、Service 和 Model 層
- **函數式服務設計**：適合無狀態的業務邏輯處理
- **完整的型別註解**：所有函數都有詳細的型別提示
- **詳細的文件字串**：遵循 Google 風格規範
- **適當的索引設計**：優化資料庫查詢效能
- **併發安全考量**：處理多使用者同時操作的情況
- **背景任務整合**：使用現有的 Celery 基礎設施

建議按照實作優先級逐步實現功能，確保每個階段都有完整的測試覆蓋和文件更新。