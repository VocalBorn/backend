# AuthService 單元測試

本目錄包含 VocalBorn 後端 AuthService 的完整單元測試套件。

## 測試覆蓋範圍

### account_service.py 測試
- ✅ `register()` - 用戶註冊功能
  - 成功註冊新用戶
  - 重複電子郵件錯誤處理
  - 郵件發送失敗處理（不影響註冊）
  - 資料庫錯誤處理
  
- ✅ `login()` - 用戶登入功能
  - 成功登入
  - 帳號不存在錯誤
  - 密碼錯誤處理
  - 未驗證帳號錯誤
  
- ✅ `update_user()` - 更新用戶資料
  - 成功更新用戶資料
  - 帳號不存在錯誤
  - 用戶資料不存在錯誤
  - 資料庫錯誤處理
  
- ✅ `update_password()` - 更新密碼
  - 成功更新密碼
  - 帳號不存在錯誤
  - 舊密碼錯誤
  - 資料庫錯誤處理
  
- ✅ `get_user_profile()` - 取得用戶資料
  - 成功取得用戶資料
  - 帳號不存在錯誤
  - 用戶資料不存在錯誤
  
- ✅ `_create_account_and_user()` - 內部函數
  - 成功建立帳號和用戶
  - 電子郵件已存在錯誤

## 執行測試

### 執行所有 AuthService 測試
```bash
# 啟動虛擬環境
source .venv/bin/activate

# 執行所有測試
python -m pytest tests/auth/ -v

# 執行特定測試檔案
python -m pytest tests/auth/test_account_service.py -v

# 執行特定測試函數
python -m pytest tests/auth/test_account_service.py::TestAccountService::test_register_success -v
```

### 測試覆蓋率
```bash
# 安裝 coverage（如果還未安裝）
pip install coverage

# 執行測試並生成覆蓋率報告
coverage run -m pytest tests/auth/
coverage report
coverage html  # 生成 HTML 報告
```

## 測試架構

### Fixtures (conftest.py)
- `mock_db_session` - Mock 資料庫會話
- `sample_account` - 範例帳號資料
- `sample_user` - 範例用戶資料
- `register_request` - 註冊請求資料
- `login_request` - 登入請求資料
- `update_user_request` - 更新用戶請求資料
- `unverified_account` - 未驗證帳號

### 測試方法
- 使用 `unittest.mock` 進行外部依賴 Mock
- 使用 `pytest.mark.asyncio` 標記異步測試
- 使用 `pytest.raises` 測試異常情況
- 使用 Mock 對象避免 SQLAlchemy 模型初始化問題

## 單元測試最佳實踐說明

### 單元測試的作用
1. **驗證業務邏輯正確性** - 確保每個函數在各種輸入下都能正確執行
2. **錯誤處理測試** - 驗證異常情況下的正確行為
3. **邊界條件測試** - 測試極值和特殊情況
4. **回歸測試** - 防止未來變更破壞現有功能
5. **活文件** - 測試本身就是最好的使用範例

### FastAPI 單元測試最佳實踐
1. **Mock 外部依賴** - 資料庫、外部 API、檔案系統等
2. **測試隔離** - 每個測試獨立運行，不影響其他測試
3. **清晰的 AAA 模式** - Arrange（準備）、Act（執行）、Assert（驗證）
4. **有意義的測試名稱** - 測試名稱應清楚描述測試場景
5. **適當的測試覆蓋率** - 重要路徑和錯誤情況都要覆蓋

## 測試結果
📊 **測試統計：21 個測試全部通過**
- 成功情況測試：7 個
- 錯誤處理測試：14 個
- 測試覆蓋率：涵蓋所有主要功能和錯誤情況

這套測試為 AuthService 提供了全面的驗證，確保認證相關功能的穩定性和可靠性。