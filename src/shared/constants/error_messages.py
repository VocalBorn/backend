"""
錯誤訊息常數
統一管理應用程式中的所有錯誤訊息
"""

# 練習相關錯誤訊息
class PracticeErrors:
    # 會話相關
    SESSION_NOT_FOUND = "練習會話不存在"
    SESSION_UNAUTHORIZED = "練習會話不存在或無權限查看"
    SESSION_ALREADY_COMPLETED = "練習會話已完成"
    SESSION_HAS_PENDING_RECORDS = "練習會話有未完成的記錄"
    SESSION_HAS_RECORDS = "練習會話包含記錄，無法刪除"
    
    # 記錄相關
    RECORD_NOT_FOUND = "練習記錄不存在"
    RECORD_UNAUTHORIZED = "練習記錄不存在或無權限查看"
    RECORD_ALREADY_COMPLETED = "練習記錄已完成"
    
    # 章節相關
    CHAPTER_NOT_FOUND = "指定的章節不存在"
    
    # 回饋相關
    FEEDBACK_NOT_FOUND = "回饋不存在"
    FEEDBACK_UNAUTHORIZED_DELETE = "無權限刪除此回饋"
    FEEDBACK_UNAUTHORIZED_VIEW = "無權限查看此患者的練習回饋"
    FEEDBACK_UNAUTHORIZED_UPDATE = "無權限更新此回饋"
    FEEDBACK_ALREADY_EXISTS = "該練習會話已有回饋，請使用更新功能"
    FEEDBACK_NO_FEEDBACK = "該練習會話沒有回饋"
    FEEDBACK_UNAUTHORIZED_CREATE = "無權限對此患者的練習進行回饋"


# 用戶和權限相關錯誤訊息
class AuthErrors:
    UNAUTHORIZED_ACCESS = "無權限存取"
    USER_NOT_FOUND = "用戶不存在"
    THERAPIST_NOT_FOUND = "治療師不存在"
    CLIENT_NOT_FOUND = "客戶不存在"
    INACTIVE_RELATIONSHIP = "治療師與患者關係已停用"
    NO_THERAPIST_PERMISSION = "非治療師無法執行此操作"


# 通用錯誤訊息
class CommonErrors:
    INVALID_UUID = "無效的UUID格式"
    VALIDATION_ERROR = "資料驗證失敗"
    DATABASE_ERROR = "資料庫操作失敗"
    INTERNAL_SERVER_ERROR = "伺服器內部錯誤"
    NOT_FOUND = "資源不存在"
    FORBIDDEN = "權限不足"


# 檔案和儲存相關錯誤訊息
class StorageErrors:
    FILE_NOT_FOUND = "檔案不存在"
    INVALID_FILE_TYPE = "檔案類型不支援"
    UPLOAD_FAILED = "檔案上傳失敗"
    FILE_TOO_LARGE = "檔案過大"
    NO_FILE_PROVIDED = "未提供檔案"