# 任務
本檔案主要在說明如何去修改 `練習系統 Practice` 的功能，並請在功能完成後於每一個項目加上 `✅`

1. **新增 AI 分析表**: 該表是為了儲存 AI 分析的結果。這個表格重點包含以下欄位：
   - `score_data`: 分數資料，這是一個 JSON 格式的欄位，用來儲存 AI 分析的分數結果。
   - `feedback_data`: 回饋資料，這是一個 String 格式的欄位，用來上面分數提供給大語言模型後進行分析的結果。
2. **調整 PracticeRecord 表**: 在 `PracticeRecord` 表中新增一個外鍵欄位 `ai_analysis_id`，用來連接到 `AIAnalysis` 表。