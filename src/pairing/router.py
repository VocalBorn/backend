from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from src.auth.services.jwt_service import verify_token

from src.auth.models import User, UserRole
from src.auth.services.permission_service import get_current_user
from src.shared.database.database import get_session
from src.pairing.services.pairing_service import (
    generate_pairing_token,
    get_therapist_tokens,
    revoke_token,
    validate_token,
    use_token,
    get_active_tokens_count
)
from src.pairing.schemas import (
    PairingTokenCreate,
    PairingTokenWithQR,
    PairingRequest,
    PairingResponse,
    TokenValidationResponse,
    TherapistTokenList
)

router = APIRouter(prefix="/pairing", tags=["pairing"])

@router.post(
    "/generate-token", 
    response_model=PairingTokenWithQR,
    summary="生成配對 Token",
    description="治療師生成配對 token，用於客戶配對",
    responses={
        200: {
            "description": "配對 token 生成成功",
            "content": {
                "application/json": {
                    "example": {
                        "token_id": "5be899d1-a444-4c75-96b3-d1d72ce92fc4",
                        "token_code": "VLZHRW45",
                        "created_at": "2025-06-19T19:10:52.642236",
                        "expires_at": "2025-06-20T19:10:52.642216",
                        "max_uses": 3,
                        "current_uses": 0,
                        "is_used": False,
                        "qr_data": "https://vocalborn.r0930514.work/pair/VLZHRW45"
                    }
                }
            }
        },
        403: {
            "description": "權限不足 - 只有治療師可以生成配對 token"
        },
        401: {
            "description": "未授權 - 需要有效的 JWT token"
        }
    }
)
async def generate_pairing_token_router(
    token_data: PairingTokenCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    治療師生成配對 token
    
    - **max_uses**: token 最大使用次數 (預設: 1)
    - **expires_in_hours**: token 有效期限(小時) (預設: 72)
    
    需要治療師權限才能使用此功能。
    """
    
    # 驗證用戶是治療師
    if current_user.role != UserRole.THERAPIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有治療師可以生成配對token"
        )
    
    return generate_pairing_token(
        session,
        therapist_id=current_user.user_id,
        token_data=token_data
    )

@router.get(
    "/my-tokens", 
    response_model=TherapistTokenList,
    summary="查看我的配對 Token 列表",
    description="治療師查看自己創建的所有配對 token",
    responses={
        200: {
            "description": "成功獲取 token 列表",
            "content": {
                "application/json": {
                    "example": {
                        "tokens": [
                            {
                                "token_id": "5be899d1-a444-4c75-96b3-d1d72ce92fc4",
                                "token_code": "VLZHRW45",
                                "created_at": "2025-06-19T19:10:52.642236",
                                "expires_at": "2025-06-20T19:10:52.642216",
                                "max_uses": 3,
                                "current_uses": 1,
                                "is_used": False
                            }
                        ],
                        "total_count": 1
                    }
                }
            }
        },
        403: {
            "description": "權限不足 - 只有治療師可以查看 token 列表"
        },
        401: {
            "description": "未授權 - 需要有效的 JWT token"
        }
    }
)
async def get_my_tokens_router(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    治療師查看自己的 token 列表
    
    返回治療師創建的所有配對 token，包括：
    - Token 基本資訊
    - 使用次數統計
    - 有效期限
    - 使用狀態
    
    需要治療師權限才能使用此功能。
    """
    
    if current_user.role != UserRole.THERAPIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有治療師可以查看token列表"
        )
    
    return get_therapist_tokens(session, current_user.user_id)

@router.delete(
    "/tokens/{token_id}",
    summary="撤銷配對 Token",
    description="治療師撤銷指定的配對 token",
    responses={
        200: {
            "description": "Token 撤銷成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Token已撤銷"
                    }
                }
            }
        },
        403: {
            "description": "權限不足 - 只有治療師可以撤銷 token"
        },
        404: {
            "description": "Token 不存在或不屬於當前治療師"
        },
        401: {
            "description": "未授權 - 需要有效的 JWT token"
        }
    }
)
async def revoke_token_router(
    token_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    治療師撤銷 token
    
    撤銷指定的配對 token，使其無法再被使用。
    只有 token 的創建者可以撤銷該 token。
    
    - **token_id**: 要撤銷的 token UUID
    
    需要治療師權限才能使用此功能。
    """
    
    if current_user.role != UserRole.THERAPIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有治療師可以撤銷token"
        )
    
    success = revoke_token(session, token_id, current_user.user_id)
    return {"success": success, "message": "Token已撤銷"}

@router.get(
    "/validate/{token_code}", 
    response_model=TokenValidationResponse,
    summary="驗證配對 Token",
    description="驗證配對 token 的有效性（公開端點，不需要認證）",
    responses={
        200: {
            "description": "Token 驗證結果",
            "content": {
                "application/json": {
                    "examples": {
                        "valid_token": {
                            "summary": "有效的 Token",
                            "value": {
                                "is_valid": True,
                                "token_code": "VLZHRW45",
                                "therapist_name": "我是語言治療師",
                                "expires_at": "2025-06-20T19:10:52.642216",
                                "remaining_uses": 3
                            }
                        },
                        "invalid_token": {
                            "summary": "無效的 Token",
                            "value": {
                                "is_valid": False,
                                "token_code": None,
                                "therapist_name": None,
                                "expires_at": None,
                                "remaining_uses": None
                            }
                        }
                    }
                }
            }
        }
    }
)
async def validate_token_router(
    token_code: str,
    session: Annotated[Session, Depends(get_session)]
):
    """
    驗證 token 有效性（公開端點，不需要認證）
    
    檢查配對 token 是否有效，並返回相關資訊：
    - Token 有效性狀態
    - 關聯的治療師名稱
    - 剩餘使用次數
    - 過期時間
    
    - **token_code**: 要驗證的 token 代碼
    
    此端點為公開端點，不需要認證即可使用。
    """
    
    return validate_token(session, token_code)

@router.post(
    "/join/{token_code}", 
    response_model=PairingResponse,
    summary="使用配對 Token 進行配對",
    description="客戶使用配對 token 與治療師建立配對關係",
    responses={
        200: {
            "description": "配對成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "配對成功",
                        "therapist_id": "ad669ac6-25ba-46ba-984f-20ab58a6ed9e",
                        "therapist_name": "我是語言治療師",
                        "paired_at": "2025-06-19T19:12:57.740395"
                    }
                }
            }
        },
        400: {
            "description": "配對失敗 - Token 無效、已過期或已用完"
        },
        403: {
            "description": "權限不足 - 只有客戶可以使用配對 token"
        },
        401: {
            "description": "未授權 - 需要有效的 JWT token"
        }
    }
)
async def join_with_token_router(
    token_code: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    客戶使用 token 進行配對
    
    客戶使用配對 token 與治療師建立配對關係。
    配對成功後，客戶可以存取該治療師的課程和服務。
    
    - **token_code**: 配對 token 代碼
    
    需要客戶權限才能使用此功能。
    """
    
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有客戶可以使用配對token"
        )
    
    return use_token(session, token_code, current_user.user_id)

@router.get(
    "/my-therapists",
    summary="查看已配對的治療師列表",
    description="客戶查看已配對的治療師列表",
    responses={
        200: {
            "description": "成功獲取治療師列表",
            "content": {
                "application/json": {
                    "example": {
                        "therapists": [
                            {
                                "therapist_id": "ad669ac6-25ba-46ba-984f-20ab58a6ed9e",
                                "therapist_name": "我是語言治療師",
                                "assigned_date": "2025-06-19T19:12:57.740395",
                                "notes": "透過配對Token建立: VLZHRW45"
                            }
                        ],
                        "total_count": 1
                    }
                }
            }
        },
        403: {
            "description": "權限不足 - 只有客戶可以查看治療師列表"
        },
        401: {
            "description": "未授權 - 需要有效的 JWT token"
        }
    }
)
async def get_my_therapists_router(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    客戶查看已配對的治療師列表
    
    返回客戶已配對的所有治療師資訊，包括：
    - 治療師基本資訊
    - 配對建立日期
    - 配對備註（如透過哪個 token 配對）
    
    需要客戶權限才能使用此功能。
    """
    
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有客戶可以查看治療師列表"
        )
    
    from src.therapist.services.therapist_service import TherapistService
    therapist_service = TherapistService(session)
    
    # 取得客戶的治療師列表
    therapist_relations = therapist_service.get_client_therapists(current_user.user_id)
    
    therapists = []
    for relation in therapist_relations:
        therapist = session.get(User, relation.therapist_id)
        if therapist:
            therapists.append({
                "therapist_id": therapist.user_id,
                "therapist_name": therapist.name,
                "assigned_date": relation.assigned_date,
                "notes": relation.notes
            })
    
    return {"therapists": therapists, "total_count": len(therapists)}

@router.get(
    "/stats",
    summary="獲取配對統計資料",
    description="治療師查看配對相關的統計資料",
    responses={
        200: {
            "description": "成功獲取統計資料",
            "content": {
                "application/json": {
                    "example": {
                        "active_tokens": 1,
                        "total_clients": 5,
                        "token_pairings": 3
                    }
                }
            }
        },
        403: {
            "description": "權限不足 - 只有治療師可以查看配對統計"
        },
        401: {
            "description": "未授權 - 需要有效的 JWT token"
        }
    }
)
async def get_pairing_stats_router(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    取得配對統計（治療師專用）
    
    返回治療師的配對相關統計資料：
    - **active_tokens**: 目前活躍的配對 token 數量
    - **total_clients**: 總客戶數量
    - **token_pairings**: 透過 token 配對的客戶數量
    
    需要治療師權限才能使用此功能。
    """
    
    if current_user.role != UserRole.THERAPIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有治療師可以查看配對統計"
        )
    
    # 取得活躍token數量
    active_tokens = get_active_tokens_count(session, current_user.user_id)

    # 取得客戶數量
    from src.therapist.services.therapist_service import TherapistService
    therapist_service = TherapistService(session)
    clients = therapist_service.get_therapist_clients(current_user.user_id)

    return {
        "active_tokens": active_tokens,
        "total_clients": len(clients),
        "token_pairings": len([c for c in clients if "配對Token" in (c.notes or "")])
    }
