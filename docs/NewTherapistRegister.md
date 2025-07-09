本文件重點放在調整語言治療師的註冊流程
# 語言治療師註冊流程調整
## 步驟
1. 在一般的註冊表單中使用 /therapist/register API 註冊新治療師，欄位包括：
```json
{
  // 使用者基本資料
  "email": "user@example.com",
  "password": "stringst",
  "name": "string",
  "gender": "male",
  "age": 150,
  // 語言治療師個人資料
  "bio": "專精於兒童語言發展治療，具有豐富的臨床經驗。",
  "education": "國立陽明交通大學語言治療學系碩士",
  "license_number": "TH123456",
  "specialization": "語言治療",
  "years_experience": 5
}
```
Response 內容請再寫一個 Schema，包含 user_id、therapist_profile_id、verification_application_id
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "verification_application_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```
（想讓目前複雜的治療師註冊流程變得更加簡單）
2. 使用者註冊後，前端會自動導向到治療師資料上傳頁面，並顯示以下訊息：
```
請上傳您的治療師證照和相關文件以完成註冊。
我們將在收到您的文件後進行審核，審核通過後
您將收到通知。
```
3. 使用者上傳證照和相關文件後，前端會呼叫 /verification/therapist-applications/{application_id}/documents/ API，本 API 無須進行登入，只需將 application_id 作為路徑參數傳入，並上傳文件。上傳的文件會被存儲在 S3 中。

4. 系統管理員即可進行審核，審核通過後，系統會自動將使用者的帳號狀態更新為「已驗證」，並發送通知給使用者。
