# VocalBorn 後端專案文件

此目錄包含 VocalBorn 語言治療學習平台後端專案的所有相關文件。

## 📁 目錄結構

### 🏗️ Architecture（架構）
包含專案的架構設計和系統設計相關文件。
- `ERD.drawio` - 資料庫實體關係圖

### 🚀 Deployment（部署）
包含專案部署相關的文件和指南。
- `celery/` - Celery 任務系統相關的部署文件
  - `CELERY_ADMIN_DEPLOYMENT.md` - Celery 管理系統部署指南
  - `CELERY_ADMIN_USAGE_EXAMPLES.md` - Celery 管理系統使用範例

### 💻 Development（開發）
包含開發過程中產生的文件，如程式碼審查、計畫和任務記錄。
- `code-review/` - 程式碼審查記錄
- `plans/` - 專案計畫文件
- `development-tasks/` - 開發任務記錄

### 📚 User Guides（使用指南）
包含各種使用者指南和 API 文件。
- `api/` - API 相關文件
  - `PracticeAPI.md` - 練習功能 API 說明
- `therapist/` - 治療師相關指南
  - `FrontendTherapistRegistrationGuide.md` - 前端治療師註冊指南
  - `NewTherapistRegister.md` - 治療師註冊流程
  - `TherapistApplicationProcess.md` - 治療師申請流程
- `testing/` - 測試相關文件
  - `service_test_templates.md` - 服務測試範本

## 📝 文件維護原則

1. **分類明確**：新文件應根據其用途放置在對應的目錄中
2. **命名規範**：使用英文檔名，避免空格，使用小寫和連字符
3. **持續更新**：定期檢查和更新文件內容，確保其準確性和時效性
4. **版本控制**：重要文件更改請記錄變更原因和日期

## 🤝 如何貢獻

如需新增或修改文件，請遵循以下步驟：
1. 確定文件應放置的正確分類
2. 使用清晰的標題和結構
3. 包含必要的範例和說明
4. 提交前檢查格式和內容正確性

---

*最後更新：2025-08-13*