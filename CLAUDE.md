# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 語言指導原則 (Language Guidelines)

**重要：在此專案中工作時，請一律使用繁體中文進行回應和說明。**

所有的回應、錯誤訊息、說明文字和註解都應該使用繁體中文，以確保與團隊的溝通一致性。

## Common Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Install dependencies
pip install -r requirements.txt

# Update requirements after adding new packages
pip freeze > requirements.txt
```

### Development Server
```bash
# Run development server
fastapi dev src/main.py
```

### Database Operations
```bash
# Apply database migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Check current database version
alembic current

# View migration history
alembic history

# Rollback to previous version
alembic downgrade -1
```

### Docker
```bash
# Run containerized application
docker run -d -p 5001:5000 vocalborn_backend
```

## Architecture Overview

This is a **FastAPI-based REST API** for VocalBorn, a speech therapy learning platform. The application serves three user types: clients (therapy seekers), therapists (service providers), and admins.

### Technology Stack
- **Python 3.13.0** with **FastAPI**
- **SQLModel** (SQLAlchemy-based) for ORM
- **PostgreSQL** database with **Alembic** migrations
- **MinIO** (S3-compatible) for file storage
- **JWT** authentication with role-based access control

### Core Application Structure

```
src/
├── main.py              # Application entry point
├── auth/                # Authentication & user management
├── therapist/           # Therapist registration & verification
├── course/              # Course content & practice sessions
├── pairing/             # Therapist-client pairing system
├── verification/        # Document verification workflow
├── chat/                # Chat functionality
├── storage/             # File storage services
│   ├── storage_service.py      # Base storage service
│   ├── audio_storage_service.py # Audio file storage
│   ├── storage_factory.py      # Storage service factory
│   └── practice_recording_service.py # Practice recording logic
└── shared/              # Shared utilities
    ├── config/          # Environment configuration
    ├── database/        # Database connection setup
    ├── services/        # Email & other services
    └── schemas/         # Common schema definitions
```

### Database Architecture

The application uses a relational database with key entities:
- **User System**: `accounts`, `users`, `email_verifications`
- **Therapist Workflow**: `therapist_profiles`, `therapist_applications`, `uploaded_documents`
- **Course Content**: `situations`, `chapters`, `sentences`, `practice_records`
- **Pairing System**: `pairing_tokens`, `therapist_clients`

### External Services
- **MinIO**: File storage for documents, audio recordings, and media files
- **Email Service**: External HTTP API for verification and password reset emails
- **PostgreSQL**: Primary database

### Storage Module
The application uses a modular storage system supporting multiple file types:
- **Document Storage**: PDF, Word, images for verification documents
- **Audio Storage**: MP3, WAV, M4A for practice recordings and course audio
- **Extensible Design**: Easy to add new storage types (video, images, etc.)

Storage services are organized by purpose:
- `get_verification_storage()` - Document verification files
- `get_practice_recording_storage()` - User practice recordings
- `get_course_audio_storage()` - Course audio content
- `practice_recording_service` - High-level practice recording operations

### Testing
The storage module includes comprehensive unit tests:
```bash
# Run all storage tests
python tests/run_storage_tests.py

# Run specific test files
pytest tests/storage/test_storage_service.py -v
pytest tests/storage/test_audio_storage_service.py -v
pytest tests/storage/test_storage_factory.py -v
pytest tests/storage/test_practice_recording_service.py -v
```

Test coverage includes:
- Storage service functionality (upload, download, delete)
- Audio file validation and processing
- Factory pattern implementation
- Practice recording business logic
- Error handling and edge cases

## Development Guidelines

### Database Changes
All database structure modifications MUST be done through Alembic migrations:
1. Modify SQLModel definitions in the codebase
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply changes: `alembic upgrade head`

### Environment Configuration
- Load `.env` file from Notion (as specified in README)
- Configuration is managed through `src/shared/config/config.py`
- Database connection setup is in `src/shared/database/database.py`

### Service Design Guidelines

#### Design Pattern Selection

**使用函數式設計（預設選擇）**：
- 簡單的 CRUD 操作
- 無狀態的業務邏輯處理
- 資料驗證和轉換
- 單純的輸入輸出處理

```python
# ✅ 函數式設計範例
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """建立新用戶"""
    # 驗證資料
    # 建立用戶
    # 返回結果
    
async def validate_email(email: str) -> bool:
    """驗證電子郵件格式"""
    # 純粹的驗證邏輯
```

**使用類別式設計（特殊情況）**：
- 需要維護連線狀態（如資料庫連線、外部服務連線）
- 複雜的配置管理
- 需要繼承和多態
- 封裝複雜狀態的服務

```python
# ✅ 類別式設計範例
class StorageService:
    """檔案儲存服務 - 需要維護 MinIO 客戶端連線"""
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self._client = self._initialize_client()
    
class EmailService:
    """電子郵件服務 - 複雜的重試邏輯和配置管理"""
    def __init__(self, config: EmailConfig):
        self.config = config
        self.retry_strategy = RetryStrategy()
```

#### Error Handling Standards

**函數式服務**：
```python
async def service_function(data: InputData) -> OutputData:
    try:
        # 業務邏輯
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="資料庫操作失敗")
```

**類別式服務**：
```python
class ServiceClass:
    def service_method(self, data: InputData) -> OutputData:
        try:
            # 業務邏輯
            return result
        except ServiceSpecificError as e:
            logger.error(f"服務錯誤: {e}")
            raise ServiceError(f"操作失敗: {e}")
```

#### Dependency Injection

**函數式服務 - 使用 FastAPI Depends**：
```python
async def service_function(
    data: InputData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 業務邏輯
```

**類別式服務 - 建構子注入**：
```python
class ServiceClass:
    def __init__(self, dependency: DependencyType):
        self.dependency = dependency

# 使用工廠函數
def get_service() -> ServiceClass:
    return ServiceClass(get_dependency())
```

#### Testing Guidelines

**函數式服務測試**：
```python
@pytest.mark.asyncio
async def test_service_function():
    # 準備測試資料
    mock_db = Mock()
    test_data = create_test_data()
    
    # 執行測試
    result = await service_function(test_data, mock_db)
    
    # 驗證結果
    assert result.status == "success"
```

**類別式服務測試**：
```python
def test_service_class():
    # 建立服務實例
    service = ServiceClass(mock_dependency)
    
    # 執行測試
    result = service.service_method(test_data)
    
    # 驗證結果
    assert result.is_valid()
```

### Commit Convention
Use conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `test:` - Testing changes
- `refactor:` - Code restructuring
- `style:` - Formatting changes
- `docs:` - Documentation updates
- `chore:` - Build process, tools, etc.

## Application Domain

VocalBorn connects speech therapists with clients through:
1. **User Registration**: Email verification workflow for all user types
2. **Therapist Verification**: Document upload and admin approval process
3. **Course Structure**: Hierarchical content (situations → chapters → sentences)
4. **Practice Sessions**: Audio recording and feedback system
5. **Pairing System**: Token-based therapist-client matching
6. **Document Management**: Secure file storage and retrieval

The application follows a modular router-based architecture with clear separation of concerns between authentication, business logic, and data access layers.