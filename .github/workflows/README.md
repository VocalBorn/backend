# VocalBorn CI/CD Pipeline 說明

## 🔄 Workflow 觸發條件

### 🌿 所有分支
- **Push 事件**：任何分支的推送都會觸發測試和代碼品質檢查
- **Pull Request**：針對 main 分支的 PR 會觸發測試和代碼品質檢查
- **手動觸發**：可透過 GitHub Actions 頁面手動執行

## 📋 執行階段

### 1. 🧪 Unit Tests (所有分支都執行)
- 設定 Python 3.13 測試環境
- 安裝專案依賴項
- 配置測試環境變數
- 執行單元測試（忽略需要外部服務的測試）
- 生成測試覆蓋率報告
- 可選的 Codecov 整合

### 2. 🔍 Code Quality (所有分支都執行)
- Black 代碼格式檢查
- isort import 排序檢查
- flake8 程式碼規範檢查
- mypy 型別檢查（可選）

### 3. 🐳 Docker Build & Push (僅 main 分支)
- **條件**：只有在推送到 `main` 分支時才執行
- **依賴**：必須等待 Unit Tests 和 Code Quality 都通過
- 多平台 Docker 映像構建（linux/amd64, linux/arm64）
- 推送到 Docker Hub
- 智能標籤管理和快取優化

## 🛡️ 安全保證

- **漸進式失敗**：任何階段失敗都會阻止後續步驟
- **分支保護**：只有測試通過的 main 分支變更才會觸發 Docker 推送
- **環境隔離**：測試使用獨立的 SQLite 測試資料庫
- **智能忽略**：跳過需要外部服務的測試，確保 CI 穩定性

## 📊 執行矩陣

| 分支類型 | Unit Tests | Code Quality | Docker Push |
|---------|------------|-------------|-------------|
| `main` | ✅ | ✅ | ✅ (測試通過後) |
| `develop` | ✅ | ✅ | ❌ |
| `feature/*` | ✅ | ✅ | ❌ |
| `fix/*` | ✅ | ✅ | ❌ |
| PR to main | ✅ | ✅ | ❌ |

## 🔧 本地測試

在推送前，建議先在本地執行測試：

```bash
# 執行單元測試
python -m pytest tests/ -v --disable-warnings \
  --ignore=tests/storage/test_audio_storage_service.py \
  --ignore=tests/therapist/test_therapist_service.py \
  -k "not test_send_email"

# 代碼格式檢查
black --check src/ tests/
isort --check-only src/ tests/
flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
```

這個設計確保了每次程式碼變更都經過嚴格的品質檢查，同時只有經過完整驗證的 main 分支變更才會部署到生產環境。