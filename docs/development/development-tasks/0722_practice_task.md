請調整 practice 路由與服務
# Task
整理路由以符合 REST API 最佳實踐：

## Session 會話管理
- **開始新的練習會話**: POST `/practice/sessions`: 需提供 Chapter ID，會回傳練習會話詳情。
- **查詢用戶練習會話列表**: GET `/practice/sessions`: 可選參數 chapter_id 來篩選特定章節，支援分頁。
- **查詢特定練習會話**: GET `/practice/sessions/{practice_session_id}`: 需提供練習會話ID，會回傳練習會話詳情。
- **刪除練習會話**: DELETE `/practice/sessions/{practice_session_id}`: 需提供練習會話ID。

## 會話記錄管理
- **查詢練習記錄**: GET `/practice/sessions/{practice_session_id}/records`: 需提供練習會話ID，會回傳該會話的所有練習記錄與對應句子ID與內容。
- **更新練習記錄**: PUT `/practice/sessions/{practice_session_id}/records/{sentence_id}`: 需提供練習會話ID和句子ID，會更新該句子的練習記錄狀態。

## 會話錄音管理
> **重要**: 確保一個練習會話裡面一句只會有一個錄音檔案。

- **上傳/更新練習錄音**: PUT `/practice/sessions/{practice_session_id}/recordings/{sentence_id}`: 需提供練習會話ID、句子ID及錄音檔案。如果錄音已存在則更新，不存在則建立（符合 PUT 冪等性原則）。
- **查詢會話所有錄音**: GET `/practice/sessions/{practice_session_id}/recordings`: 需提供練習會話ID，會回傳該會話的所有錄音檔案資訊。
- **查詢特定句子錄音**: GET `/practice/sessions/{practice_session_id}/recordings/{sentence_id}`: 需提供練習會話ID和句子ID，會回傳該句子的錄音檔案。
- **刪除練習錄音**: DELETE `/practice/sessions/{practice_session_id}/recordings/{sentence_id}`: 需提供練習會話ID和句子ID。

## 章節相關查詢
- **查詢章節練習會話**: GET `/practice/chapters/{chapter_id}/sessions`: 需提供章節ID，會回傳該章節的所有練習會話，支援分頁。

## API 設計原則
1. **資源命名**: 使用複數形式（sessions, records, recordings）
2. **HTTP 方法**: 
   - POST: 建立新資源
   - GET: 查詢資源
   - PUT: 更新/建立資源（冪等性）
   - DELETE: 刪除資源
3. **路徑層次**: 遵循資源的自然層次關係
4. **錯誤處理**: 返回適當的 HTTP 狀態碼和錯誤訊息
5. **分頁支援**: 對於列表查詢提供 skip 和 limit 參數

