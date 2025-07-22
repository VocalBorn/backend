# Task 
請調整 練習系統 相關流程
## 流程
1. **開始練習**：提供 Chapter ID，調用 `/practice/start` 端點開始練習，該練習會話即會被建立，裡面會有 練習會話ID 等資訊。
2. **上傳練習錄音**：提供 練習會話ID 和 句子ID 以及錄音的檔案，並且上傳到 `/practice/upload/{practice_session_id}/{sentence_id}` 端點。

## 其他可用端點
- **取得練習記錄**：提供 練習會話ID，調用 `/practice/records/{practice_session_id}` 端點來取得該練習會話的所有練習記錄與對應句子ID與內容。
- **刪除練習會話**：提供 練習會話ID，調用 `/practice/delete/{practice_session_id}` 端點來刪除該練習會話。