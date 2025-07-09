# 寫給前端的語言治療師註冊流程說明書

本文件旨在向前端開發者說明新的、簡化後的語言治療師註冊流程。此流程將使用者基本資料與治療師專業檔案的提交合併為單一步驟，並簡化了文件上傳的驗證機制。

## 流程步驟

### 1. 註冊新治療師帳號 (Register New Therapist Account)

這是治療師註冊流程的第一步，也是唯一需要前端提交所有註冊資訊的 API。

*   **端點 (Endpoint):** `POST /therapist/register`
*   **請求方法 (Method):** `POST`
*   **請求主體 (Request Body):** `application/json`
    *   請使用 `TherapistRegisterRequest` Schema。此 Schema 包含了使用者基本資料和治療師專業檔案的所有欄位。
    *   **欄位說明:**
        *   `email` (string, EmailStr): 使用者電子郵件，必須是有效格式。
        *   `password` (string): 密碼，至少8個字元，需包含大小寫字母、數字和特殊字元。
        *   `name` (string): 使用者姓名。
        *   `gender` (enum: "male", "female", "other"): 使用者性別。
        *   `age` (integer): 使用者年齡。
        *   `license_number` (string): 治療師執照號碼，**必填且唯一**。
        *   `specialization` (string, optional): 專長領域。
        *   `bio` (string, optional): 個人簡介。
        *   `years_experience` (integer, optional): 執業年資。
        *   `education` (string, optional): 學歷。
    *   **範例請求 (Example Request):**
        ```json
        {
          "email": "therapist.new.example@example.com",
          "password": "SecurePassword123!",
          "name": "王小明",
          "gender": "male",
          "age": 30,
          "license_number": "TH987654",
          "specialization": "兒童語言發展",
          "bio": "專精於兒童語言發展治療，具有豐富的臨床經驗。",
          "years_experience": 5,
          "education": "國立陽明交通大學語言治療學系碩士"
        }
        ```
*   **回應主體 (Response Body):** `application/json`
    *   請使用 `TherapistRegistrationResponse` Schema。
    *   **欄位說明:**
        *   `user_id` (UUID): 新建立的使用者唯一識別碼。
        *   `verification_application_id` (UUID): 關聯到此註冊的驗證申請唯一識別碼。
    *   **範例回應 (Example Response):**
        ```json
        {
          "user_id": "550e8400-e29b-41d4-a716-446655440001",
          "verification_application_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
        }
        ```
*   **重要提示:**
    *   此 API 呼叫會一次性完成使用者帳號建立、治療師個人檔案建立，以及一個待處理的驗證申請。
    *   使用者帳號的初始角色為 `CLIENT`，並在驗證申請通過後才會被提升為 `THERAPIST`。
    *   此步驟完成後，前端應引導使用者進入文件上傳流程。

### 2. 上傳驗證文件 (Upload Verification Documents)

在完成註冊後，前端應提示使用者上傳必要的驗證文件。

*   **端點 (Endpoint):** `POST /verification/therapist-applications/{application_id}/documents/`
*   **請求方法 (Method):** `POST`
*   **路徑參數 (Path Parameter):**
    *   `application_id` (UUID): 從步驟 1 的回應中取得的 `verification_application_id`。
*   **請求主體 (Request Body):** `multipart/form-data`
    *   **表單欄位 (Form Fields):**
        *   `document_type` (string, enum): 文件的類型。目前支援的類型包括：
            *   `therapist_certificate` (治療師證書)
            *   `id_card_front` (身份證正面)
            *   `id_card_back` (身份證反面)
        *   `file` (file): 要上傳的檔案。
    *   **範例 `curl` 指令 (Example `curl` command):**
        ```bash
        curl -X POST "http://your-backend-url/verification/therapist-applications/YOUR_APPLICATION_ID/documents/" \
          -H "Content-Type: multipart/form-data" \
          -F "document_type=therapist_certificate" \
          -F "file=@/path/to/your/certificate.pdf"
        ```
        *請將 `YOUR_APPLICATION_ID` 替換為實際的 `verification_application_id`。*
        *請將 `/path/to/your/certificate.pdf` 替換為您要上傳的檔案路徑。*
*   **驗證 (Authentication):** **此 API 無須進行登入 (不需要 JWT Token)。** 前端可以直接呼叫此端點。
*   **重要提示:**
    *   文件上傳後，後端會將檔案儲存到 MinIO (S3 相容儲存)。
    *   每次上傳文件，相關的驗證申請狀態會被重置為 `PENDING` (待處理)，等待管理員審核。
    *   前端應引導使用者上傳所有必要的文件類型。

### 後續流程

1.  **管理員審核:** 使用者上傳所有文件後，系統管理員將會審核這些文件。
2.  **狀態更新:** 審核通過後，系統會自動將使用者的帳號狀態更新為「已驗證」，並將其角色提升為 `THERAPIST`。
3.  **通知:** 使用者將會收到審核結果的通知。
4.  **前端處理:** 前端可以根據 `verification_application_id` 查詢驗證申請的狀態 (`GET /verification/therapist-applications/me` 或管理員介面)，並向使用者顯示「待審核」或「已通過」等訊息。
