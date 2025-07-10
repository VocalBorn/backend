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