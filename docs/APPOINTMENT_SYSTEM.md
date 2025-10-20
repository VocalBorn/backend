****# VocalBorn 預約系統說明文件

## 目錄

1. [系統概述](#系統概述)
2. [資料模型](#資料模型)
3. [功能詳解](#功能詳解)
4. [業務規則](#業務規則)
5. [API 參考](#api-參考)
6. [常見使用場景](#常見使用場景)

---

## 系統概述

### 簡介

VocalBorn 預約系統是一個專為語言治療平台設計的預約管理系統，支援患者與治療師之間的預約排程、時間管理和週期性預約功能。

### 系統角色

系統支援三種使用者角色：

- **患者（CLIENT）**：申請預約、修改預約、取消預約、建立週期性預約
- **治療師（THERAPIST）**：管理預約申請、設定可用時間、封鎖特定時段
- **管理員（ADMIN）**：系統設定管理、查看所有預約、統計報告、強制取消預約

### 核心功能

1. **預約管理**：患者可申請預約，治療師接受或拒絕
2. **時間管理**：治療師設定工作時間和封鎖時段
3. **週期性預約**：支援每週、每兩週、每月的週期性預約
4. **預約修改**：患者可申請修改已確認的預約時間
5. **歷史記錄**：完整記錄所有預約變更歷史
6. **系統設定**：管理員可配置全域業務規則

---

## 資料模型

### 預約狀態（AppointmentStatus）

預約系統使用以下狀態來追蹤預約的生命週期：

| 狀態 | 說明 | 可轉換至 |
|------|------|----------|
| `PENDING` | 待確認 | `CONFIRMED`, `REJECTED` |
| `CONFIRMED` | 已確認 | `PENDING_MODIFICATION`, `CANCELLED_BY_*`, `COMPLETED`, `NO_SHOW` |
| `REJECTED` | 已拒絕 | 無（終止狀態） |
| `CANCELLED_BY_CLIENT` | 患者取消 | 無（終止狀態） |
| `CANCELLED_BY_THERAPIST` | 治療師取消 | 無（終止狀態） |
| `CANCELLED_BY_ADMIN` | 管理員取消 | 無（終止狀態） |
| `AUTO_CANCELLED` | 自動取消 | 無（終止狀態） |
| `PENDING_MODIFICATION` | 待修改確認 | `CONFIRMED`, `MODIFICATION_REJECTED` |
| `MODIFICATION_REJECTED` | 修改被拒絕 | `CANCELLED_BY_*` |
| `COMPLETED` | 已完成 | 無（終止狀態） |
| `NO_SHOW` | 未出席 | 無（終止狀態） |

### 週期性模式（RecurrencePattern）

| 模式 | 說明 |
|------|------|
| `WEEKLY` | 每週重複 |
| `BIWEEKLY` | 每兩週重複 |
| `MONTHLY` | 每月重複 |

### 資料表結構

#### 1. Appointment（預約主表）

存儲所有預約的基本資訊。

**主要欄位**：
- `appointment_id`（UUID）：預約唯一識別碼
- `client_id`（UUID）：患者 ID
- `therapist_id`（UUID）：治療師 ID
- `appointment_time`（datetime）：預約時間
- `duration_minutes`（int）：預約時長（分鐘），預設 60
- `status`（AppointmentStatus）：預約狀態
- `notes`（string）：備註（最多 500 字）
- `cancellation_reason`（string）：取消原因
- `modification_requested_time`（datetime）：請求修改的新時間
- `modification_reason`（string）：修改原因
- `recurring_appointment_id`（UUID）：關聯的週期性預約 ID
- `auto_cancel_task_id`（string）：自動取消任務 ID
- `created_at`（datetime）：建立時間
- `updated_at`（datetime）：更新時間

#### 2. RecurringAppointment（週期性預約主表）

存儲週期性預約的配置。

**主要欄位**：
- `recurring_id`（UUID）：週期性預約唯一識別碼
- `client_id`（UUID）：患者 ID
- `therapist_id`（UUID）：治療師 ID
- `start_date`（date）：開始日期
- `end_date`（date）：結束日期
- `appointment_time`（time）：預約時間
- `duration_minutes`（int）：預約時長
- `recurrence_pattern`（RecurrencePattern）：重複模式
- `notes`（string）：備註
- `is_active`（bool）：是否活躍
- `created_at`（datetime）：建立時間
- `updated_at`（datetime）：更新時間

#### 3. AppointmentAvailability（治療師可用時間表）

存儲治療師的工作時間設定。

**主要欄位**：
- `availability_id`（UUID）：可用時間唯一識別碼
- `therapist_id`（UUID）：治療師 ID
- `day_of_week`（int）：星期幾（0=週日, 1=週一, ..., 6=週六）
- `start_time`（time）：開始時間
- `end_time`（time）：結束時間
- `effective_date`（date）：生效日期
- `expiry_date`（date）：失效日期（可選）
- `is_active`（bool）：是否活躍
- `buffer_minutes`（int）：緩衝時間（分鐘）
- `created_at`（datetime）：建立時間
- `updated_at`（datetime）：更新時間

#### 4. BlockedTimeSlot（封鎖時段表）

存儲治療師封鎖的特定時段（例如休假、會議）。

**主要欄位**：
- `blocked_id`（UUID）：封鎖時段唯一識別碼
- `therapist_id`（UUID）：治療師 ID
- `blocked_date`（date）：封鎖日期
- `start_time`（time）：開始時間
- `end_time`（time）：結束時間
- `reason`（string）：原因（最多 200 字）
- `notes`（string）：備註（最多 500 字）
- `is_active`（bool）：是否活躍
- `created_at`（datetime）：建立時間
- `updated_at`（datetime）：更新時間

#### 5. AppointmentHistory（預約歷史記錄表）

記錄所有預約的變更歷史。

**主要欄位**：
- `history_id`（UUID）：歷史記錄唯一識別碼
- `appointment_id`（UUID）：預約 ID
- `action`（string）：動作類型（create, modify, cancel 等）
- `old_status`（string）：舊狀態
- `new_status`（string）：新狀態
- `old_appointment_time`（datetime）：舊預約時間
- `new_appointment_time`（datetime）：新預約時間
- `changed_by_user_id`（UUID）：操作者 ID
- `reason`（string）：原因
- `extra_data`（string）：額外資料（JSON 字串）
- `created_at`（datetime）：建立時間

#### 6. AppointmentSystemSettings（預約系統設定表）

存儲系統全域設定。

**主要欄位**：
- `setting_id`（UUID）：設定唯一識別碼
- `setting_key`（string）：設定鍵（唯一）
- `setting_value`（string）：設定值
- `description`（string）：描述
- `is_active`（bool）：是否活躍
- `created_at`（datetime）：建立時間
- `updated_at`（datetime）：更新時間

**預設系統設定**：
- `minimum_advance_hours`：最少提前預約小時數（預設 24）
- `modification_deadline_hours`：修改期限小時數（預設 12）
- `auto_cancel_timeout_hours`：自動取消超時小時數（預設 12）
- `work_time_start`：工作時間開始（預設 08:00:00）
- `work_time_end`：工作時間結束（預設 20:00:00）

---

## 功能詳解

### 患者功能

#### 1. 建立預約

**端點**：`POST /appointments`

**功能說明**：
- 患者申請新的治療預約
- 預約狀態自動設為 `PENDING`（待確認）
- 系統會驗證預約時間的有效性

**驗證規則**：
- 預約時間必須至少提前 `minimum_advance_hours` 小時
- 預約時間必須在系統設定的工作時間內
- 預約時間不能與治療師的現有預約衝突

**請求範例**：
```json
{
  "therapist_id": "550e8400-e29b-41d4-a716-446655440000",
  "appointment_time": "2024-10-20T14:00:00",
  "duration_minutes": 60,
  "notes": "希望加強發音練習"
}
```

**回應範例**：
```json
{
  "appointment_id": "123e4567-e89b-12d3-a456-426614174000",
  "client_id": "...",
  "therapist_id": "550e8400-e29b-41d4-a716-446655440000",
  "appointment_time": "2024-10-20T14:00:00",
  "duration_minutes": 60,
  "status": "pending",
  "notes": "希望加強發音練習",
  "client_name": "王小明",
  "therapist_name": "李治療師",
  "created_at": "2024-10-16T10:30:00",
  "updated_at": "2024-10-16T10:30:00"
}
```

#### 2. 查看預約列表

**端點**：`GET /appointments`

**功能說明**：
- 查看當前患者的所有預約記錄
- 支援狀態、日期範圍篩選
- 支援分頁

**查詢參數**：
- `status`（選填）：預約狀態篩選
- `date_from`（選填）：開始日期
- `date_to`（選填）：結束日期
- `page`（選填）：頁碼，預設 1
- `page_size`（選填）：每頁數量，預設 20

#### 3. 查看預約詳情

**端點**：`GET /appointments/{appointment_id}`

**功能說明**：
- 查看指定預約的詳細資訊
- 只能查看自己相關的預約

#### 4. 申請修改預約

**端點**：`PUT /appointments/{appointment_id}/modify`

**功能說明**：
- 患者申請修改已確認的預約時間
- 預約狀態變更為 `PENDING_MODIFICATION`
- 需要治療師重新確認

**限制條件**：
- 只能修改狀態為 `CONFIRMED` 的預約
- 必須在預約前 `modification_deadline_hours` 小時申請
- 新時間必須通過所有驗證規則

**請求範例**：
```json
{
  "new_appointment_time": "2024-10-20T15:00:00",
  "modification_reason": "臨時有事，希望延後一小時"
}
```

#### 5. 取消預約

**端點**：`DELETE /appointments/{appointment_id}`

**功能說明**：
- 患者取消自己的預約
- 預約狀態變更為 `CANCELLED_BY_CLIENT`

**請求範例**：
```json
{
  "cancellation_reason": "因臨時出差無法參加"
}
```

#### 6. 查詢治療師可用時間

**端點**：`GET /therapists/{therapist_id}/availability`

**功能說明**：
- 查詢指定治療師在特定日期範圍內的可用時間段
- 自動排除已預約、封鎖時段和工作時間外的時段

**查詢參數**：
- `date_from`（必填）：查詢開始日期
- `date_to`（必填）：查詢結束日期
- `duration`（選填）：預約時長（分鐘），預設 60

**限制**：
- 查詢範圍不能超過 30 天

**回應範例**：
```json
{
  "therapist_id": "550e8400-e29b-41d4-a716-446655440000",
  "therapist_name": "李治療師",
  "available_slots": [
    {
      "date": "2024-10-20",
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "duration_minutes": 60
    },
    {
      "date": "2024-10-20",
      "start_time": "10:00:00",
      "end_time": "11:00:00",
      "duration_minutes": 60
    }
  ],
  "total_slots": 2
}
```

#### 7. 建立週期性預約

**端點**：`POST /recurring-appointments`

**功能說明**：
- 患者建立週期性預約
- 系統自動生成一系列預約記錄
- 每個預約都需要治療師確認

**請求範例**：
```json
{
  "therapist_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-10-21",
  "end_date": "2024-12-31",
  "appointment_time": "14:00:00",
  "duration_minutes": 60,
  "recurrence_pattern": "weekly",
  "notes": "每週固定治療課程"
}
```

**重複模式**：
- `weekly`：每週重複
- `biweekly`：每兩週重複
- `monthly`：每月重複

**行為說明**：
- 系統會計算所有預約時間點
- 如果某些時間點有衝突，會跳過該時間點
- 如果所有時間點都無法建立，會返回錯誤

#### 8. 查看週期性預約

**端點**：`GET /recurring-appointments`

**功能說明**：
- 查看當前患者的所有週期性預約設定

**查詢參數**：
- `is_active`（選填）：是否只顯示活躍的週期性預約，預設 true

#### 9. 取消週期性預約

**端點**：`DELETE /recurring-appointments/{recurring_id}`

**功能說明**：
- 取消週期性預約設定
- 自動取消所有相關的未來預約（狀態為 `PENDING`、`CONFIRMED` 或 `PENDING_MODIFICATION`）

---

### 治療師功能

#### 1. 查看預約列表

**端點**：`GET /therapist/appointments`

**功能說明**：
- 治療師查看自己的所有預約
- 包含患者資訊
- 支援狀態、日期範圍篩選和分頁

#### 2. 接受預約申請

**端點**：`PUT /therapist/appointments/{appointment_id}/accept`

**功能說明**：
- 治療師接受患者的預約申請
- 預約狀態從 `PENDING` 變更為 `CONFIRMED`

**限制條件**：
- 只能接受狀態為 `PENDING` 的預約
- 只能接受自己的預約

#### 3. 拒絕預約申請

**端點**：`PUT /therapist/appointments/{appointment_id}/reject`

**功能說明**：
- 治療師拒絕患者的預約申請
- 預約狀態從 `PENDING` 變更為 `REJECTED`
- 需要提供拒絕原因

**請求範例**：
```json
{
  "rejection_reason": "該時段已有其他安排"
}
```

#### 4. 接受預約修改申請

**端點**：`PUT /therapist/appointments/{appointment_id}/modification/accept`

**功能說明**：
- 治療師接受患者的預約時間修改申請
- 預約時間更新為請求的新時間
- 預約狀態從 `PENDING_MODIFICATION` 變更為 `CONFIRMED`

**限制條件**：
- 只能接受狀態為 `PENDING_MODIFICATION` 的預約

#### 5. 拒絕預約修改申請

**端點**：`PUT /therapist/appointments/{appointment_id}/modification/reject`

**功能說明**：
- 治療師拒絕患者的預約時間修改申請
- 預約時間保持原樣
- 預約狀態從 `PENDING_MODIFICATION` 變更為 `MODIFICATION_REJECTED`
- 需要提供拒絕原因

**請求範例**：
```json
{
  "rejection_reason": "新時間無法配合"
}
```

#### 6. 設定工作時間

**端點**：`POST /therapist/availability`

**功能說明**：
- 治療師設定自己的可用工作時間
- 按星期幾設定
- 可設定生效日期和失效日期

**請求範例**：
```json
{
  "day_of_week": 1,
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "effective_date": "2024-10-20",
  "expiry_date": null,
  "buffer_minutes": 15
}
```

**欄位說明**：
- `day_of_week`：星期幾（0=週日, 1=週一, ..., 6=週六）
- `buffer_minutes`：每個預約之間的緩衝時間（分鐘）

**限制**：
- 同一天只能有一個活躍的可用時間設定

#### 7. 查看工作時間設定

**端點**：`GET /therapist/availability`

**功能說明**：
- 查看自己的工作時間設定
- 支援日期範圍篩選

#### 8. 更新工作時間設定

**端點**：`PUT /therapist/availability/{availability_id}`

**功能說明**：
- 更新已存在的工作時間設定

**請求範例**：
```json
{
  "start_time": "08:00:00",
  "end_time": "18:00:00",
  "buffer_minutes": 10
}
```

#### 9. 刪除工作時間設定

**端點**：`DELETE /therapist/availability/{availability_id}`

**功能說明**：
- 軟刪除工作時間設定（設為非活躍）

#### 10. 封鎖特定時段

**端點**：`POST /therapist/blocked-slots`

**功能說明**：
- 治療師封鎖特定時段（例如休假、會議）
- 封鎖的時段不會出現在可用時間查詢中

**請求範例**：
```json
{
  "blocked_date": "2024-10-25",
  "start_time": "14:00:00",
  "end_time": "16:00:00",
  "reason": "參加研討會",
  "notes": "全天會議"
}
```

**驗證規則**：
- 封鎖時段不能與現有預約衝突

#### 11. 查看封鎖時段

**端點**：`GET /therapist/blocked-slots`

**功能說明**：
- 查看自己的封鎖時段設定
- 支援日期範圍篩選

#### 12. 刪除封鎖時段

**端點**：`DELETE /therapist/blocked-slots/{blocked_id}`

**功能說明**：
- 軟刪除封鎖時段（設為非活躍）

#### 13. 回應週期性預約申請

**端點**：`PUT /therapist/recurring/{recurring_id}/respond`

**功能說明**：
- 治療師對週期性預約申請進行回應
- 可選擇全部接受或個別處理

**查詢參數**：
- `accept_all`（必填）：是否接受所有預約

**請求範例（全部接受）**：
```
PUT /therapist/recurring/{recurring_id}/respond?accept_all=true
```

**請求範例（個別處理）**：
```json
{
  "accept_all": false,
  "individual_responses": {
    "2024-10-23T14:00:00": "accept",
    "2024-10-30T14:00:00": "reject",
    "2024-11-06T14:00:00": "accept"
  }
}
```

**回應範例**：
```json
{
  "message": "週期性預約回應處理完成",
  "recurring_id": "...",
  "total_appointments": 10,
  "accepted_count": 9,
  "rejected_count": 1
}
```

---

### 管理員功能

#### 1. 查看所有預約

**端點**：`GET /admin/appointments`

**功能說明**：
- 管理員查看系統中所有預約
- 支援多維度篩選（狀態、治療師、患者、日期範圍）

**查詢參數**：
- `status`（選填）：預約狀態
- `therapist_id`（選填）：治療師 ID
- `client_id`（選填）：患者 ID
- `date_from`（選填）：開始日期
- `date_to`（選填）：結束日期
- `page`（選填）：頁碼
- `page_size`（選填）：每頁數量

#### 2. 查看預約詳情

**端點**：`GET /admin/appointments/{appointment_id}`

**功能說明**：
- 管理員查看任意預約的詳細資訊

#### 3. 強制取消預約

**端點**：`PUT /admin/appointments/{appointment_id}/force-cancel`

**功能說明**：
- 管理員強制取消預約
- 用於緊急情況或系統維護
- 預約狀態變更為 `CANCELLED_BY_ADMIN`

**請求範例**：
```json
{
  "reason": "系統維護，暫停服務",
  "notify_users": true
}
```

#### 4. 查看系統設定

**端點**：`GET /admin/system/settings`

**功能說明**：
- 查看預約系統的全域設定

**回應範例**：
```json
{
  "minimum_advance_hours": 24,
  "modification_deadline_hours": 12,
  "auto_cancel_timeout_hours": 12,
  "work_time_start": "08:00:00",
  "work_time_end": "20:00:00"
}
```

#### 5. 更新系統設定

**端點**：`PUT /admin/system/settings`

**功能說明**：
- 更新預約系統的全域設定
- 影響所有業務規則

**請求範例**：
```json
{
  "minimum_advance_hours": 48,
  "modification_deadline_hours": 24,
  "work_time_start": "09:00:00",
  "work_time_end": "18:00:00"
}
```

#### 6. 預約統計報告

**端點**：`GET /admin/appointments/statistics`

**功能說明**：
- 管理員查看預約統計數據
- 支援按不同維度分組

**查詢參數**：
- `date_from`（選填）：統計開始日期
- `date_to`（選填）：統計結束日期
- `group_by`（選填）：分組方式（overall, therapist, time），預設 overall

**回應範例**：
```json
{
  "overall_statistics": {
    "total_appointments": 150,
    "pending_appointments": 20,
    "confirmed_appointments": 100,
    "cancelled_appointments": 15,
    "completed_appointments": 10,
    "no_show_appointments": 5,
    "average_duration": 60.5,
    "most_popular_times": []
  },
  "therapist_statistics": [
    {
      "therapist_id": "...",
      "therapist_name": "李治療師",
      "total_appointments": 50,
      "confirmed_rate": 85.0,
      "cancellation_rate": 10.0,
      "no_show_rate": 5.0
    }
  ],
  "date_range": "2024-09-16 到 2024-10-16"
}
```

---

## 業務規則

### 時區處理

系統使用 `Asia/Taipei` 時區（台北時間）作為預設時區。

**時區處理邏輯**：
1. 當 `appointment_time` 帶有時區資訊時，系統會將當前時間轉換為相同時區進行比較
2. 當 `appointment_time` 沒有時區資訊時，系統假定為本地時間（無時區）
3. 所有時間驗證都確保時區一致性，避免時區差異導致的錯誤

**程式碼範例**（參考 [schemas.py:16-31](src/appointment/schemas.py#L16-L31)）：
```python
now = datetime.datetime.now()
if v.tzinfo is not None:
    # 如果輸入有時區資訊，將 now 轉換為相同時區
    if now.tzinfo is None:
        now = pytz.timezone('Asia/Taipei').localize(now)
else:
    # 如果輸入沒有時區資訊，確保 now 也沒有
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)
```

### 預約驗證規則

當患者建立或修改預約時，系統會執行以下驗證：

#### 1. 提前預約時間檢查

- 預約時間必須至少提前 `minimum_advance_hours` 小時（預設 24 小時）
- 範例：如果現在是 10/16 10:00，預約時間必須在 10/17 10:00 之後

#### 2. 工作時間檢查

- 預約時間必須在系統設定的工作時間內
- 預設工作時間：08:00:00 - 20:00:00
- 只檢查預約開始時間，不檢查結束時間

#### 3. 時間衝突檢查

系統會檢查預約時間是否與治療師的現有預約衝突：

- 檢查範圍：狀態為 `PENDING`、`CONFIRMED` 或 `PENDING_MODIFICATION` 的預約
- 衝突判定：兩個預約的時間區間有重疊

**衝突檢查邏輯**（參考 [appointment_service.py:134-160](src/appointment/services/appointment_service.py#L134-L160)）：
```python
# 檢查時間衝突
end_time = appointment_time + datetime.timedelta(minutes=duration_minutes)

stmt = select(Appointment).where(
    and_(
        Appointment.therapist_id == therapist_id,
        or_(
            Appointment.status == AppointmentStatus.PENDING,
            Appointment.status == AppointmentStatus.CONFIRMED,
            Appointment.status == AppointmentStatus.PENDING_MODIFICATION
        ),
        or_(
            and_(
                Appointment.appointment_time < end_time,
                Appointment.appointment_time + func.make_interval(...) > appointment_time
            )
        )
    )
)
```

### 修改和取消的期限限制

#### 修改期限

- 患者只能在預約前 `modification_deadline_hours` 小時（預設 12 小時）申請修改
- 範例：如果預約時間是 10/20 14:00，患者必須在 10/20 02:00 之前申請修改
- 只有狀態為 `CONFIRMED` 的預約才能申請修改

#### 取消限制

- 患者可以隨時取消自己的預約
- 治療師可以隨時取消預約
- 管理員可以強制取消任何預約
- 已結束的預約（已取消、已完成、未出席、已拒絕）無法再次取消

### 可用時間計算邏輯

當患者查詢治療師可用時間時，系統會：

1. **獲取治療師的工作時間設定**
   - 根據查詢日期範圍和星期幾匹配
   - 檢查生效日期和失效日期

2. **排除封鎖時段**
   - 查詢該日期的所有活躍封鎖時段
   - 從可用時間中排除

3. **排除現有預約**
   - 查詢該日期的所有活躍預約（`PENDING`、`CONFIRMED`、`PENDING_MODIFICATION`）
   - 從可用時間中排除

4. **計算時間段**
   - 根據預約時長（`duration_minutes`）分割可用時間
   - 考慮緩衝時間（`buffer_minutes`）

**時間段計算邏輯**（參考 [availability_service.py:419-474](src/appointment/services/availability_service.py#L419-L474)）：
```python
while current_time + duration_delta <= end_datetime:
    slot_end_time = current_time + duration_delta

    # 檢查是否與封鎖時段衝突
    # 檢查是否與現有預約衝突

    if not is_blocked:
        slots.append(AvailableTimeSlot(...))

    # 移動到下一個時間段（包含緩衝時間）
    current_time += duration_delta + buffer_delta
```

### 週期性預約處理

#### 日期計算

系統根據週期模式計算所有預約日期：

- **每週（WEEKLY）**：從開始日期起，每 7 天一個預約
- **每兩週（BIWEEKLY）**：從開始日期起，每 14 天一個預約
- **每月（MONTHLY）**：從開始日期起，每月同一天一個預約
  - 特殊處理：如果目標月份沒有該日期（例如 1/31 到 2 月），使用該月的最後一天

#### 預約建立

1. 系統計算所有預約日期
2. 為每個日期建立個別的 `Appointment` 記錄
3. 每個預約都需要通過驗證（時間、衝突檢查）
4. 如果某個日期無法建立預約（例如時間衝突），會跳過該日期並記錄
5. 如果所有日期都無法建立預約，週期性預約建立失敗

#### 治療師回應

治療師可以選擇：
1. **全部接受**：所有待確認的預約都變為已確認
2. **個別處理**：為每個預約單獨選擇接受或拒絕

### 歷史記錄

系統會自動記錄所有預約的變更：

**記錄的動作類型**：
- `create`：建立預約
- `modify_request`：申請修改
- `accept`：接受預約
- `reject`：拒絕預約
- `accept_modification`：接受修改
- `reject_modification`：拒絕修改
- `cancel`：取消預約

**記錄內容**：
- 舊狀態和新狀態
- 舊預約時間和新預約時間
- 操作者 ID
- 操作原因
- 額外資料（JSON 格式）

---

## API 參考

### 患者端點

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/appointments` | 建立預約 |
| GET | `/appointments` | 查看預約列表 |
| GET | `/appointments/{appointment_id}` | 查看預約詳情 |
| PUT | `/appointments/{appointment_id}/modify` | 申請修改預約 |
| DELETE | `/appointments/{appointment_id}` | 取消預約 |
| GET | `/therapists/{therapist_id}/availability` | 查詢治療師可用時間 |
| POST | `/recurring-appointments` | 建立週期性預約 |
| GET | `/recurring-appointments` | 查看週期性預約 |
| DELETE | `/recurring-appointments/{recurring_id}` | 取消週期性預約 |

### 治療師端點

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/therapist/appointments` | 查看預約列表 |
| PUT | `/therapist/appointments/{appointment_id}/accept` | 接受預約申請 |
| PUT | `/therapist/appointments/{appointment_id}/reject` | 拒絕預約申請 |
| PUT | `/therapist/appointments/{appointment_id}/modification/accept` | 接受修改申請 |
| PUT | `/therapist/appointments/{appointment_id}/modification/reject` | 拒絕修改申請 |
| POST | `/therapist/availability` | 設定工作時間 |
| GET | `/therapist/availability` | 查看工作時間設定 |
| PUT | `/therapist/availability/{availability_id}` | 更新工作時間設定 |
| DELETE | `/therapist/availability/{availability_id}` | 刪除工作時間設定 |
| POST | `/therapist/blocked-slots` | 封鎖特定時段 |
| GET | `/therapist/blocked-slots` | 查看封鎖時段 |
| DELETE | `/therapist/blocked-slots/{blocked_id}` | 刪除封鎖時段 |
| PUT | `/therapist/recurring/{recurring_id}/respond` | 回應週期性預約 |

### 管理員端點

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/admin/appointments` | 查看所有預約 |
| GET | `/admin/appointments/{appointment_id}` | 查看預約詳情 |
| PUT | `/admin/appointments/{appointment_id}/force-cancel` | 強制取消預約 |
| GET | `/admin/appointments/statistics` | 預約統計報告 |
| GET | `/admin/system/settings` | 查看系統設定 |
| PUT | `/admin/system/settings` | 更新系統設定 |

---

## 常見使用場景

### 場景 1：患者預約流程

1. **患者查詢治療師可用時間**
   ```
   GET /therapists/{therapist_id}/availability?date_from=2024-10-20&date_to=2024-10-27&duration=60
   ```

2. **患者申請預約**
   ```
   POST /appointments
   {
     "therapist_id": "...",
     "appointment_time": "2024-10-20T14:00:00",
     "duration_minutes": 60,
     "notes": "希望加強發音練習"
   }
   ```
   - 系統建立預約，狀態為 `PENDING`
   - 系統記錄歷史：action = "create"

3. **治療師接受預約**
   ```
   PUT /therapist/appointments/{appointment_id}/accept
   ```
   - 預約狀態變更為 `CONFIRMED`
   - 系統記錄歷史：action = "accept"

4. **患者參加治療課程**
   - 預約完成後，管理員或系統將狀態標記為 `COMPLETED`

### 場景 2：患者申請修改預約流程

1. **患者申請修改**
   ```
   PUT /appointments/{appointment_id}/modify
   {
     "new_appointment_time": "2024-10-20T15:00:00",
     "modification_reason": "臨時有事，希望延後一小時"
   }
   ```
   - 系統檢查：狀態必須為 `CONFIRMED`
   - 系統檢查：必須在修改期限內（預設預約前 12 小時）
   - 系統檢查：新時間通過所有驗證
   - 預約狀態變更為 `PENDING_MODIFICATION`
   - 原預約時間保持不變，新時間存入 `modification_requested_time`
   - 系統記錄歷史：action = "modify_request"

2. **治療師接受修改**
   ```
   PUT /therapist/appointments/{appointment_id}/modification/accept
   ```
   - 預約時間更新為新時間
   - 預約狀態變更為 `CONFIRMED`
   - 清空 `modification_requested_time` 和 `modification_reason`
   - 系統記錄歷史：action = "accept_modification"

3. **治療師拒絕修改**
   ```
   PUT /therapist/appointments/{appointment_id}/modification/reject
   {
     "rejection_reason": "新時間無法配合"
   }
   ```
   - 預約時間保持原樣
   - 預約狀態變更為 `MODIFICATION_REJECTED`
   - 清空 `modification_requested_time` 和 `modification_reason`
   - 系統記錄歷史：action = "reject_modification"

### 場景 3：治療師管理時間表流程

1. **治療師設定每週一的工作時間**
   ```
   POST /therapist/availability
   {
     "day_of_week": 1,
     "start_time": "09:00:00",
     "end_time": "17:00:00",
     "effective_date": "2024-10-20",
     "expiry_date": null,
     "buffer_minutes": 15
   }
   ```

2. **治療師封鎖特定時段（例如參加會議）**
   ```
   POST /therapist/blocked-slots
   {
     "blocked_date": "2024-10-25",
     "start_time": "14:00:00",
     "end_time": "16:00:00",
     "reason": "參加研討會",
     "notes": "全天會議"
   }
   ```

3. **患者查詢可用時間時，系統會自動排除**
   - 治療師的工作時間外
   - 封鎖時段
   - 已有預約的時段

### 場景 4：週期性預約處理流程

1. **患者建立每週週期性預約**
   ```
   POST /recurring-appointments
   {
     "therapist_id": "...",
     "start_date": "2024-10-21",
     "end_date": "2024-12-31",
     "appointment_time": "14:00:00",
     "duration_minutes": 60,
     "recurrence_pattern": "weekly",
     "notes": "每週固定治療課程"
   }
   ```
   - 系統計算所有預約日期：10/21, 10/28, 11/04, 11/11, ...
   - 為每個日期建立個別預約，狀態為 `PENDING`
   - 如果某些日期有衝突，跳過該日期

2. **治療師全部接受**
   ```
   PUT /therapist/recurring/{recurring_id}/respond?accept_all=true
   ```
   - 所有待確認的預約狀態變更為 `CONFIRMED`

3. **治療師個別處理**
   ```
   PUT /therapist/recurring/{recurring_id}/respond?accept_all=false
   {
     "individual_responses": {
       "2024-10-21T14:00:00": "accept",
       "2024-10-28T14:00:00": "reject",
       "2024-11-04T14:00:00": "accept"
     }
   }
   ```

4. **患者取消週期性預約**
   ```
   DELETE /recurring-appointments/{recurring_id}
   ```
   - 週期性預約設為非活躍
   - 所有相關的未來預約自動取消

### 場景 5：管理員系統維護流程

1. **管理員查看系統統計**
   ```
   GET /admin/appointments/statistics?date_from=2024-09-01&date_to=2024-09-30&group_by=therapist
   ```

2. **管理員調整系統設定**
   ```
   PUT /admin/system/settings
   {
     "minimum_advance_hours": 48,
     "modification_deadline_hours": 24
   }
   ```
   - 所有新建立的預約都會使用新設定

3. **管理員強制取消預約（系統維護）**
   ```
   PUT /admin/appointments/{appointment_id}/force-cancel
   {
     "reason": "系統維護，暫停服務",
     "notify_users": true
   }
   ```

---

## 技術細節

### 程式碼結構

```
src/appointment/
├── models.py                    # 資料模型定義
├── schemas.py                   # Pydantic 模型（請求/回應）
├── services/
│   ├── appointment_service.py   # 預約核心業務邏輯
│   ├── availability_service.py  # 可用時間管理
│   ├── recurring_service.py     # 週期性預約處理
│   ├── email_service.py         # 郵件通知服務
│   └── task_service.py          # 背景任務服務
└── routers/
    ├── client_appointment_router.py    # 患者路由
    ├── therapist_appointment_router.py # 治療師路由
    └── admin_appointment_router.py     # 管理員路由
```

### 依賴服務

- **資料庫**：PostgreSQL（使用 SQLModel ORM）
- **時區處理**：pytz 庫（Asia/Taipei）
- **API 框架**：FastAPI
- **驗證**：Pydantic

### 資料庫遷移

使用 Alembic 管理資料庫結構變更：

```bash
# 進入 alembic 目錄
cd alembic

# 套用遷移
uv run alembic upgrade head

# 建立新遷移（如有模型變更）
uv run alembic revision --autogenerate -m "描述"
```

### 權限控制

系統使用基於角色的存取控制（RBAC）：

- 每個端點都檢查使用者角色
- 患者只能查看和操作自己的預約
- 治療師只能查看和操作自己相關的預約
- 管理員可以查看和操作所有資源

---

## 附錄

### 預約狀態流程圖

```
[患者建立預約] → PENDING
                    ↓
          ┌─────────┴─────────┐
          ↓                   ↓
    CONFIRMED             REJECTED
          ↓
    ┌─────┴─────┬─────────┬──────────┐
    ↓           ↓         ↓          ↓
COMPLETED   NO_SHOW   CANCELLED   PENDING_MODIFICATION
                                       ↓
                              ┌────────┴────────┐
                              ↓                 ↓
                         CONFIRMED    MODIFICATION_REJECTED
```

### 系統設定說明

| 設定鍵 | 說明 | 預設值 | 範圍 |
|--------|------|--------|------|
| `minimum_advance_hours` | 最少提前預約小時數 | 24 | 1-168 |
| `modification_deadline_hours` | 修改期限小時數 | 12 | 1-72 |
| `auto_cancel_timeout_hours` | 自動取消超時小時數 | 12 | 1-48 |
| `work_time_start` | 工作時間開始 | 08:00:00 | - |
| `work_time_end` | 工作時間結束 | 20:00:00 | - |

### 錯誤代碼

| HTTP 狀態碼 | 說明 | 常見原因 |
|------------|------|----------|
| 400 | 請求錯誤 | 驗證失敗、超過期限、狀態不允許 |
| 403 | 權限不足 | 角色不符、無權限操作 |
| 404 | 資源不存在 | 預約不存在、治療師不存在 |
| 409 | 衝突 | 時間衝突、重複設定 |

### 常見問題

**Q: 患者可以修改多少次預約？**
A: 沒有次數限制，但必須在修改期限內（預約前 12 小時，可由管理員調整）。

**Q: 週期性預約的所有預約都需要治療師確認嗎？**
A: 是的，每個預約都是獨立的，都需要治療師確認。治療師可以選擇全部接受或個別處理。

**Q: 如果治療師的工作時間變更，會影響已確認的預約嗎？**
A: 不會。已確認的預約不受工作時間設定變更的影響。工作時間設定只影響新的預約申請和可用時間查詢。

**Q: 緩衝時間（buffer_minutes）的作用是什麼？**
A: 緩衝時間是治療師在每個預約之間的休息或準備時間。例如，如果設定 15 分鐘緩衝，一個 60 分鐘的預約結束後，下一個可用時段是 75 分鐘之後。

**Q: 系統如何處理時區？**
A: 系統預設使用 `Asia/Taipei` 時區。當處理帶有時區資訊的時間時，系統會自動轉換為相同時區進行比較，確保時間計算的正確性。

---

## 版本資訊

**文件版本**：1.0
**最後更新**：2024-10-16
**對應系統版本**：VocalBorn Backend v1.0

---

## 聯絡資訊

如有任何問題或建議，請聯絡開發團隊。
