# 治療師模組程式碼審查報告

## 整體評估摘要

治療師模組整體設計符合基本的架構原則，但存在多項需要改進的重要問題。程式碼結構清晰，權限控制完善，但在安全性、效能優化、錯誤處理和測試覆蓋率方面有改進空間。

**總體評分：7.0/10**

## 詳細問題分析

### 🔴 **重大問題（Critical）**

#### 1. 安全漏洞 - 執照號碼查詢權限不當
**問題位置**：`src/therapist/router.py:105-116`
```python
@router.get("/profile/{user_id}")
async def get_therapist_profile_by_id(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.VIEW_THERAPIST_PROFILE)),
```

**問題**：任何擁有 `VIEW_THERAPIST_PROFILE` 權限的使用者都可以查看其他治療師的完整檔案，包括敏感的執照號碼。這違反了個人資料保護原則。

**建議修正**：
```python
@router.get("/profile/{user_id}")
async def get_therapist_profile_by_id(
    user_id: UUID,
    current_user: User = Depends(require_permission(Permission.VIEW_THERAPIST_PROFILE)),
    session: Session = Depends(get_session)
):
    # 新增權限檢查：只有管理員或本人可以查看完整檔案
    if (current_user.role != UserRole.ADMIN and 
        current_user.user_id != user_id):
        # 返回公開資訊版本，隱藏敏感資料
        return get_public_therapist_profile(user_id, session)
    
    # 返回完整檔案（包含敏感資訊）
    return get_full_therapist_profile(user_id, session)
```

#### 2. 資料外洩風險 - 回應中包含敏感資訊
**問題位置**：`src/therapist/schemas.py:103-128`
```python
class TherapistProfileResponse(BaseModel):
    license_number: Optional[str]  # 執照號碼應該限制存取
```

**問題**：`TherapistProfileResponse` 直接暴露執照號碼等敏感資訊，沒有根據使用者角色進行資料過濾。

**建議修正**：
```python
class PublicTherapistProfileResponse(BaseModel):
    """公開的治療師檔案回應（隱藏敏感資訊）"""
    therapist_name: str
    specialization: Optional[str]
    bio: Optional[str]
    years_of_experience: Optional[int]
    languages: Optional[str]
    # 不包含 license_number 等敏感資訊

class FullTherapistProfileResponse(BaseModel):
    """完整的治療師檔案回應（包含敏感資訊）"""
    therapist_name: str
    specialization: Optional[str]
    bio: Optional[str]
    years_of_experience: Optional[int]
    languages: Optional[str]
    license_number: Optional[str]  # 僅限管理員或本人查看
    # 其他敏感資訊
```

#### 3. 註冊流程安全問題
**問題位置**：`src/therapist/services/therapist_service.py:21-84`

**問題**：
- 在檢查執照號碼重複性之後，實際建立檔案之前可能發生競態條件
- 密碼驗證邏輯依賴外部函數，缺乏本地驗證

**建議修正**：
```python
async def register_therapist(
    therapist_data: TherapistRegisterRequest, 
    session: Session
) -> User:
    """安全的治療師註冊流程"""
    try:
        # 開始資料庫交易
        with session.begin():
            # 再次檢查執照號碼唯一性（防止競態條件）
            existing_therapist = session.exec(
                select(TherapistProfile)
                .where(TherapistProfile.license_number == therapist_data.license_number)
                .with_for_update()  # 鎖定該行
            ).first()
            
            if existing_therapist:
                raise HTTPException(
                    status_code=400, 
                    detail="此執照號碼已被註冊"
                )
            
            # 本地密碼強度驗證
            if not _validate_password_strength(therapist_data.password):
                raise HTTPException(
                    status_code=400,
                    detail="密碼強度不符要求"
                )
            
            # 建立用戶和檔案
            user = _create_user_account(therapist_data, session)
            profile = _create_therapist_profile(user.user_id, therapist_data, session)
            
            return user
            
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"治療師註冊失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="註冊過程中發生錯誤，請稍後再試"
        )

def _validate_password_strength(password: str) -> bool:
    """本地密碼強度驗證"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True
```

### 🟡 **主要問題（Major）**

#### 4. N+1 查詢效能問題
**問題位置**：`src/therapist/router.py:186-202`
```python
for therapist in therapists:
    profile = therapist_service.get_therapist_profile(session, therapist.user_id)
```

**問題**：在 `get_all_therapists` 端點中，對每個治療師都執行一次額外的資料庫查詢來獲取檔案資訊。

**建議修正**：
```python
async def get_all_therapists_optimized(
    session: Session,
    skip: int = 0,
    limit: int = 10
) -> List[TherapistWithProfileResponse]:
    """優化的治療師列表查詢（避免 N+1 問題）"""
    # 使用 JOIN 一次性載入用戶和檔案資料
    results = session.exec(
        select(User, TherapistProfile)
        .join(TherapistProfile, User.user_id == TherapistProfile.user_id)
        .where(User.role == UserRole.THERAPIST)
        .offset(skip)
        .limit(limit)
    ).all()
    
    therapist_responses = []
    for user, profile in results:
        therapist_responses.append(
            TherapistWithProfileResponse(
                user_id=user.user_id,
                name=user.name,
                email=get_user_email(user.account_id, session),
                profile=profile
            )
        )
    
    return therapist_responses
```

#### 5. 缺乏適當的資料驗證
**問題位置**：`src/therapist/services/therapist_service.py:115-142`

**問題**：`update_therapist_profile` 函數缺乏對資料完整性的深度驗證

**建議新增驗證**：
```python
def validate_therapist_profile_data(profile_data: TherapistProfileUpdate) -> None:
    """治療師檔案資料驗證"""
    # 執照號碼格式驗證
    if profile_data.license_number:
        if not re.match(r'^[A-Z]{2}\d{6}$', profile_data.license_number):
            raise HTTPException(
                status_code=400,
                detail="執照號碼格式無效（應為：XX123456）"
            )
    
    # 經驗年數合理性檢查
    if profile_data.years_of_experience is not None:
        if profile_data.years_of_experience < 0 or profile_data.years_of_experience > 50:
            raise HTTPException(
                status_code=400,
                detail="經驗年數應在 0-50 年之間"
            )
    
    # 專業領域有效性檢查
    valid_specializations = [
        "言語治療", "語言治療", "吞嚥治療", 
        "構音治療", "語言發展", "溝通障礙"
    ]
    if (profile_data.specialization and 
        profile_data.specialization not in valid_specializations):
        raise HTTPException(
            status_code=400,
            detail=f"專業領域必須是: {', '.join(valid_specializations)} 之一"
        )
```

#### 6. 錯誤訊息資訊洩露
**問題位置**：`src/therapist/services/therapist_service.py:82-84`
```python
raise HTTPException(
    status_code=500,
    detail=f"Failed to register therapist: {str(e)}"
)
```

**問題**：直接將內部錯誤訊息暴露給用戶端，可能洩露系統內部結構資訊。

**建議修正**：
```python
except HTTPException:
    # HTTPException 可以直接拋出
    raise
except Exception as e:
    # 記錄詳細錯誤供內部除錯
    logger.error(f"治療師註冊失敗: {str(e)}, 請求資料: {therapist_data}")
    
    # 向用戶端返回安全的錯誤訊息
    raise HTTPException(
        status_code=500,
        detail="註冊過程中發生錯誤，請稍後再試"
    )
```

### 🟢 **次要問題（Minor）**

#### 7. 文件字串不完整
**問題**：部分函數缺乏完整的 Google 風格文件字串

**建議改進**：
```python
async def update_therapist_profile(
    user_id: str,
    profile_data: TherapistProfileUpdate,
    session: Session
) -> TherapistProfileResponse:
    """更新治療師檔案資訊
    
    Args:
        user_id: 治療師用戶 ID
        profile_data: 要更新的檔案資料
        session: 資料庫會話
        
    Returns:
        TherapistProfileResponse: 更新後的治療師檔案
        
    Raises:
        HTTPException: 當治療師不存在或更新失敗時
        ValidationError: 當輸入資料驗證失敗時
    """
```

#### 8. 硬編碼值
**問題位置**：`src/therapist/services/therapist_service.py:39`
```python
role=UserRole.CLIENT, # Start as client, promote upon approval
```

**建議改進**：
```python
# 在 config.py 中新增
DEFAULT_THERAPIST_REGISTRATION_ROLE = os.getenv(
    "DEFAULT_THERAPIST_REGISTRATION_ROLE", 
    "CLIENT"
)

# 在服務中使用
role=UserRole(settings.DEFAULT_THERAPIST_REGISTRATION_ROLE)
```

## 測試覆蓋率評估

### 現狀
- 僅有業務邏輯 Mock 測試
- 缺乏完整的整合測試
- 缺乏 API 端點測試
- 缺乏安全性測試

### 建議測試增強
```
tests/therapist/
├── test_therapist_service.py      ✅ (已存在，需增強)
├── test_therapist_router.py       ❌ (需新增)
├── test_security.py               ❌ (需新增)
└── test_integration.py            ❌ (需新增)
```

**新增測試範例**：
```python
# test_security.py
def test_profile_access_permission():
    """測試檔案存取權限控制"""
    # 測試非管理員無法查看他人敏感資訊
    pass

def test_license_number_privacy():
    """測試執照號碼隱私保護"""
    # 確保執照號碼只對授權用戶顯示
    pass

# test_therapist_router.py
def test_register_therapist_api():
    """測試治療師註冊 API 端點"""
    pass

def test_get_therapist_profile_api():
    """測試取得治療師檔案 API 端點"""
    pass
```

## 效能考量

### 主要效能問題
1. **N+1 查詢問題**：`get_all_therapists` 端點存在明顯的 N+1 查詢
2. **缺乏快取機制**：頻繁存取的治療師檔案資料沒有快取
3. **資料庫索引**：需要確認執照號碼等常用查詢欄位的索引配置

### 效能優化建議
```python
# 1. 實作快取機制
from functools import lru_cache

@lru_cache(maxsize=256)
def get_cached_therapist_profile(user_id: str) -> TherapistProfileResponse:
    """快取治療師檔案資料"""
    pass

# 2. 資料庫索引建議
class TherapistProfile(SQLModel, table=True):
    license_number: str = Field(index=True, unique=True)  # 新增索引
    specialization: Optional[str] = Field(index=True)     # 新增索引
    years_of_experience: Optional[int] = Field(index=True) # 新增索引
```

## 符合 CLAUDE.md 指南檢查

### ✅ **符合項目**
- 函數命名遵循慣例（如 `therapist_service`）
- 使用繁體中文註釋和文件
- 型別註解基本完整
- 單檔案行數控制良好（最大檔案 244 行）

### ❌ **不符合項目**
- 部分函數缺乏完整的 Google 風格文件字串
- 錯誤處理不夠細緻，有資訊洩露風險
- 缺乏對資料庫結構變更的相關服務檢查

## 立即行動建議

### 🚨 **緊急處理（24小時內）**
1. **修復安全漏洞**：限制治療師檔案的存取權限，避免敏感資訊洩露
2. **實作資料過濾**：基於使用者角色過濾敏感資訊
3. **加強註冊流程安全**：新增交易鎖定和競態條件防護

### 📝 **短期改進（1-2週）**
1. **優化資料庫查詢**：解決 N+1 查詢問題
2. **加強資料驗證**：增加業務邏輯層級的驗證規則
3. **改善錯誤處理**：避免敏感資訊洩露
4. **新增安全性測試**：確保權限控制正確性

### 🎯 **中期優化（1個月）**
1. **實施快取機制**：提升查詢效能
2. **完善測試覆蓋**：新增 API 端點和整合測試
3. **新增審計日誌**：記錄敏感操作
4. **優化資料庫索引**：提升查詢效能

## 積極評價

### ✅ **優點**
1. **模組化架構**：程式碼結構清晰，職責分離良好
2. **權限系統**：基本的權限控制機制完善
3. **資料模型設計**：SQLModel 使用得當，關聯設計合理
4. **API 設計**：REST API 設計符合慣例，文件完整

## 總結

治療師模組提供了良好的基礎架構，但在安全性和效能方面需要重要改進才能達到生產環境的品質標準。

特別需要關注的是敏感資料的存取控制問題，這直接影響到用戶隱私和系統安全。建議優先處理安全漏洞，然後逐步完善效能和測試覆蓋率。

---
*檢視日期：2025-08-12*
*檢視人員：Code Reviewer Agent*