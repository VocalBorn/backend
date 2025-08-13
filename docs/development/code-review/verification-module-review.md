# 驗證模組程式碼審查報告

## 總體評估摘要

此驗證模組是一個治療師資格驗證系統，整體結構良好，但存在一些關鍵的安全和品質問題需要解決。模組遵循了 FastAPI 的最佳實踐和專案的架構模式，但在某些方面需要改進。

**總體評分：6.0/10**

## 關鍵問題分析

### 🔴 **嚴重安全漏洞（Critical）**

#### 1. 檔案上傳端點缺乏身份驗證
**問題位置**：`src/verification/router.py:53-64`
```python
async def upload_document(
    application_id: uuid.UUID,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    # 缺少身份驗證依賴
    db_session: Session = Depends(get_session)
):
```

**風險**：任何人都可以上傳任意檔案到系統，可能導致惡意檔案攻擊、儲存空間濫用

**建議修正**：
```python
@router.post(
    "/therapist-applications/{application_id}/documents/",
    response_model=UploadedDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="為指定的申請上傳驗證文件"
)
async def upload_document(
    application_id: uuid.UUID,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),  # 新增身份驗證
    db_session: Session = Depends(get_session)
):
    """為指定的申請上傳文件（例如身分證、證書等）。需要使用者登入。"""
    application = await services.get_application_by_id(application_id, db_session)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到指定的申請")
    
    # 確保只有申請所有者或管理員可以上傳文件
    if application.user_id != current_user.user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="無權限存取此申請"
        )
    
    return await services.upload_verification_document(application, document_type, file, db_session)
```

#### 2. 缺乏檔案類型和大小驗證
**問題位置**：`src/verification/services.py:53-101`
**問題**：未驗證上傳檔案的類型、大小和內容

**建議修正**：
```python
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_upload_file(file: UploadFile) -> None:
    """驗證上傳檔案的安全性"""
    # 檢查檔案大小
    file_content = await file.read()
    await file.seek(0)  # 重置指針
    
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"檔案大小不能超過 {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # 檢查 MIME 類型
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支援的檔案格式"
        )
    
    # 檢查檔案內容（簡單的魔術數字檢查）
    if file.content_type.startswith('image/'):
        magic_numbers = {
            b'\xff\xd8\xff': 'image/jpeg',
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'GIF87a': 'image/gif',
            b'GIF89a': 'image/gif',
        }
        
        file_header = file_content[:10]
        is_valid = any(file_header.startswith(magic) for magic in magic_numbers.keys())
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="檔案內容與宣告類型不符"
            )
```

#### 3. 完全缺乏測試
**問題**：驗證模組沒有任何單元測試或整合測試

**建議新增測試結構**：
```
tests/verification/
├── test_verification_services.py
├── test_verification_router.py
├── test_file_upload_security.py
└── test_application_flow.py
```

### 🟡 **主要問題（Major）**

#### 4. 缺乏 `create_application` 端點
**問題**：服務層有 `create_application` 函數，但路由層沒有對應端點

**建議新增**：
```python
@router.post(
    "/therapist-applications/",
    response_model=TherapistApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="建立治療師驗證申請"
)
async def create_application(
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_session)
):
    """建立新的治療師驗證申請"""
    return await services.create_application(current_user, db_session)
```

#### 5. 不一致的錯誤處理模式
**問題位置**：`src/verification/services.py:171`
```python
print(f"User with ID {application.user_id} not found for application {application.id}")
```

**問題**：使用 `print` 進行錯誤記錄而非專業的日誌系統

**建議修正**：
```python
import logging

logger = logging.getLogger(__name__)

# 替換 print 語句
if user:
    user.role = UserRole.THERAPIST
    db_session.add(user)
else:
    logger.warning(f"User with ID {application.user_id} not found for application {application.id}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="申請批准過程中發生內部錯誤"
    )
```

#### 6. 資料庫交易管理不完整
**問題位置**：`src/verification/services.py:153-177`
**問題**：`approve_application` 函數中的複雜操作沒有使用資料庫交易

**建議修正**：
```python
async def approve_application(
    application: TherapistApplication, 
    admin_user_id: uuid.UUID, 
    db_session: Session
) -> TherapistApplication:
    """批准申請並更新用戶角色為治療師"""
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="只有待處理的申請才能被批准"
        )
    
    try:
        with db_session.begin():
            # Update application status
            application.status = ApplicationStatus.APPROVED
            application.reviewed_by_id = admin_user_id
            db_session.add(application)

            # Update user's role to THERAPIST
            user = db_session.get(User, application.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="找不到對應的使用者"
                )
            
            user.role = UserRole.THERAPIST
            db_session.add(user)
            
            db_session.commit()
            
        db_session.refresh(application)
        db_session.refresh(user)
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        db_session.rollback()
        logger.error(f"批准申請失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="申請批准過程中發生錯誤"
        )
```

### 🟢 **次要問題（Minor）**

#### 7. 型別註解不完整
**問題位置**：`src/verification/schemas.py:27-28`
**問題**：使用了 `str | None` 而非 `Optional[str]`，雖然功能相同但不一致

**建議**：統一使用 `Optional` 型別

#### 8. 文件字串不完整
**問題**：多數服務函數缺乏詳細的 Google 風格文件字串

**建議修正範例**：
```python
async def create_application(current_user: User, db_session: Session) -> TherapistApplication:
    """建立新的治療師驗證申請
    
    檢查使用者是否有資格申請成為治療師，並建立新的申請記錄。
    
    Args:
        current_user: 當前登入的使用者物件
        db_session: 資料庫會話物件
    
    Returns:
        TherapistApplication: 新建立的申請物件
    
    Raises:
        HTTPException: 當使用者無資格申請或已有有效申請時
    """
```

#### 9. 缺乏輸入驗證
**問題位置**：`src/verification/services.py:62`
**問題**：檔案名稱處理可能不安全

**建議修正**：
```python
import re

def get_safe_file_extension(filename: str) -> str:
    """安全地提取檔案擴展名"""
    if not filename or '.' not in filename:
        return 'bin'
    
    # 只取最後一個點後的內容，並限制長度
    extension = filename.split('.')[-1].lower()
    
    # 只允許安全的擴展名
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'}
    if extension not in allowed_extensions:
        return 'bin'
    
    # 防止路徑遍歷攻擊
    extension = re.sub(r'[^a-zA-Z0-9]', '', extension)
    return extension[:10]  # 限制長度
```

## 效能考量

### 現有問題
1. **檔案上傳效能**：目前實作是同步的，大檔案上傳可能阻塞
2. **資料庫查詢最佳化**：部分查詢缺少適當的索引策略

### 改進建議
```python
# 1. 非同步檔案處理
import aiofiles

async def save_file_async(file_content: bytes, file_path: str) -> None:
    """非同步儲存檔案"""
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)

# 2. 檔案上傳進度追蹤
class FileUploadProgress:
    def __init__(self, total_size: int):
        self.total_size = total_size
        self.uploaded_size = 0
    
    def update(self, chunk_size: int):
        self.uploaded_size += chunk_size
        progress = (self.uploaded_size / self.total_size) * 100
        return progress
```

## 符合專案 CLAUDE.md 指南檢查

### ✅ **符合項目**
- 使用繁體中文註解和錯誤訊息
- Router 函數遵循命名慣例
- 使用 SQLModel 和 FastAPI 最佳實踐
- 程式碼結構清晰，關注點分離良好

### ❌ **不符合項目**
- 缺乏完整的型別註解
- 文件字串不符合 Google 風格
- 缺乏單元測試
- 錯誤處理使用 print 而非日誌系統

## 立即行動建議

### 🚨 **緊急處理（24小時內）**
1. **修復安全漏洞**：為檔案上傳端點新增身份驗證
2. **實作檔案驗證**：新增檔案類型和大小驗證
3. **加強權限控制**：確保只有授權用戶可以操作申請

### 📝 **短期改進（1-2週）**
1. **改善錯誤處理和日誌**：替換 print 語句為專業日誌
2. **新增缺失功能**：建立 `create_application` 路由端點
3. **改善資料庫交易管理**：確保操作的原子性

### 🎯 **中期優化（1個月）**
1. **建立測試套件**：撰寫單元測試和整合測試
2. **提升程式碼品質**：統一型別註解風格、新增完整文件字串
3. **效能優化**：實作非同步檔案處理和進度追蹤

## 總結

此驗證模組具有良好的基礎架構，遵循了 FastAPI 最佳實踐和專案架構模式。然而，存在關鍵的安全問題，特別是檔案上傳的身份驗證和檔案驗證機制。

建議立即處理安全漏洞，然後逐步完善錯誤處理、測試覆蓋率和程式碼品質。完成這些改進後，這將是一個安全且可靠的治療師驗證系統。

---
*檢視日期：2025-08-12*
*檢視人員：Code Reviewer Agent*