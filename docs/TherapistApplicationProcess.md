## 語言治療師申請流程 API 串接說明 

本文件旨在指導前端開發者如何串接後端 API，以實現使用者申請成為語言治療師的功能。整個流程分為兩個主要階段：**提交個人檔案資訊** 和 **上傳驗證文件**。

### 流程概述

1.  **使用者填寫個人檔案資訊**：使用者在前端介面填寫個人簡介、學歷、資歷、專注領域、執照號碼等文字資訊。
2.  **提交個人檔案資訊**：前端將這些文字資訊提交到 `POST /therapist/apply` API。
    *   此 API 會建立或更新使用者的 `TherapistProfile`。
    *   **重要**：此 API 在後端會自動檢查或建立一個與該使用者相關的 `TherapistApplication` (驗證申請)。
    *   API 回應中會包含更新後的 `TherapistProfile`，其中包含 `verification_application_id`。
3.  **取得驗證申請 ID**：前端需要獲取這個 `verification_application_id`，以便後續上傳文件。如果前端沒有從 `POST /therapist/apply` 的回應中獲取，也可以透過 `GET /verification/therapist-applications/me` 再次取得。
4.  **使用者上傳驗證文件**：使用者根據要求上傳相關文件 (例如身分證正反面、語言治療師證書等)。
5.  **提交驗證文件**：前端將每個文件單獨提交到 `POST /verification/therapist-applications/{application_id}/documents/` API。
    *   每次上傳一個文件，並指定其 `document_type`。
6.  **後續審核**：文件上傳完成後，後端管理員將會對申請進行審核。前端可以透過 `GET /verification/therapist-applications/me` 查詢申請狀態。

### API 端點詳情

#### 1. 提交個人檔案資訊

*   **目的**：提交治療師的個人簡介、學歷、資歷、專注領域、執照號碼等文字資訊，並啟動或連結驗證申請。
*   **HTTP 方法**：`POST`
*   **URL**：`/therapist/apply`
*   **請求 Body (JSON)**：`TherapistApplicationRequest` Schema
    ```json
    {
        "license_number": "TH123456",
        "specialization": "語言治療",
        "bio": "專精於兒童語言發展治療，具有豐富的臨床經驗。",
        "years_experience": 5,
        "education": "國立陽明交通大學語言治療學系碩士"
    }
    ```
*   **回應 Body (JSON)**：`TherapistProfileResponse` Schema
    ```json
    {
        "profile_id": "550e8400-e29b-41d4-a716-446655440005",
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "license_number": "TH123456",
        "specialization": "語言治療",
        "bio": "專精於兒童語言發展治療，具有豐富的臨床經驗。",
        "years_experience": 5,
        "education": "國立陽明交通大學語言治療學系碩士",
        "verification_application_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", // <-- 重要：用於後續文件上傳
        "created_at": "2025-05-01T06:03:56.458985",
        "updated_at": "2025-05-01T06:03:56.459284"
    }
    ```
*   **成功狀態碼**：`200 OK`
*   **錯誤處理**：
    *   `400 Bad Request`：資料驗證失敗 (例如執照號碼重複、格式錯誤)。
    *   `404 Not Found`：使用者不存在。
    *   `403 Forbidden`：使用者角色不允許申請 (例如管理員)。

#### 2. 取得當前使用者的驗證申請

*   **目的**：獲取當前登入使用者的最新驗證申請資訊，特別是 `application_id`。
*   **HTTP 方法**：`GET`
*   **URL**：`/verification/therapist-applications/me`
*   **請求參數**：無
*   **回應 Body (JSON)**：`TherapistApplicationRead` Schema
    ```json
    {
        "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", // <-- 這個 ID 就是 application_id
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "status": "pending", // "pending", "action_required", "approved", "rejected"
        "documents": [
            // 已上傳的文件列表
            {
                "id": "doc-id-1",
                "document_type": "id_card_front",
                "created_at": "2025-05-01T06:03:56.458985"
            }
        ],
        "rejection_reason": null,
        "reviewed_by_id": null,
        "created_at": "2025-05-01T06:03:56.458985",
        "updated_at": "2025-05-01T06:03:56.459284"
    }
    ```
*   **成功狀態碼**：`200 OK`
*   **錯誤處理**：
    *   `404 Not Found`：當前使用者沒有任何驗證申請。

#### 3. 上傳驗證文件

*   **目的**：為指定的驗證申請上傳單個文件。
*   **HTTP 方法**：`POST`
*   **URL**：`/verification/therapist-applications/{application_id}/documents/`
    *   `{application_id}`：從步驟 1 或步驟 2 獲取的驗證申請 ID。
*   **請求 Body (multipart/form-data)**：
    *   `document_type` (Form Field): 文件的類型。
        *   可選值：`id_card_front`, `id_card_back`, `therapist_certificate`
    *   `file` (File Field): 要上傳的文件本身。
*   **範例 (使用 JavaScript 的 `FormData`)**：
    ```javascript
    const formData = new FormData();
    formData.append('document_type', 'therapist_certificate'); // 或 'id_card_front', 'id_card_back'
    formData.append('file', yourFileObject); // yourFileObject 是 <input type="file"> 獲取到的 File 物件

    fetch(`/verification/therapist-applications/${applicationId}/documents/`, {
        method: 'POST',
        body: formData,
        // 通常不需要手動設置 Content-Type，瀏覽器會自動設置 multipart/form-data
        headers: {
            'Authorization': `Bearer ${yourAuthToken}`
        }
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
    ```
*   **回應 Body (JSON)**：`UploadedDocumentRead` Schema
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440006",
        "document_type": "therapist_certificate",
        "created_at": "2025-05-01T06:03:56.458985"
    }
    ```
*   **成功狀態碼**：`201 Created`
*   **錯誤處理**：
    *   `404 Not Found`：找不到指定的 `application_id`。
    *   `403 Forbidden`：使用者無權操作此申請。
    *   `500 Internal Server Error`：文件上傳失敗 (例如 MinIO 服務問題)。

### 總結

前端應引導使用者先完成個人檔案資訊的提交，然後再根據後端返回的 `verification_application_id` 或透過查詢 API 獲取的 `application_id`，分階段上傳所需的驗證文件。這樣可以確保資料的完整性和流程的順暢。
