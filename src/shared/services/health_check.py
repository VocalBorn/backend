"""
服務健康檢查模組

在系統啟動時檢查關鍵外部服務（PostgreSQL、Redis、MinIO）的可用性
"""

import asyncio
import logging
from typing import Dict, Any
import redis
from sqlmodel import Session, create_engine, text
from minio import Minio
from minio.error import S3Error
from src.shared.config.config import get_settings

logger = logging.getLogger(__name__)


class HealthCheckError(Exception):
    """健康檢查異常"""
    pass


async def check_database_health() -> Dict[str, Any]:
    """檢查 PostgreSQL 資料庫健康狀態"""
    settings = get_settings()
    start_time = asyncio.get_event_loop().time()
    
    try:
        # 建立資料庫連線
        engine = create_engine(
            settings.database_url,
            connect_args={"connect_timeout": 5}
        )
        
        with Session(engine) as session:
            # 執行簡單查詢測試連線
            result = session.exec(text("SELECT 1")).first()
            
        end_time = asyncio.get_event_loop().time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        logger.info(f"資料庫健康檢查成功，回應時間: {response_time}ms")
        return {
            "status": "healthy",
            "service": "postgresql",
            "response_time_ms": response_time,
            "message": "資料庫連線正常"
        }
        
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        error_msg = f"資料庫健康檢查失敗: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "unhealthy",
            "service": "postgresql",
            "response_time_ms": response_time,
            "message": error_msg,
            "error": str(e)
        }


async def check_redis_health() -> Dict[str, Any]:
    """檢查 Redis 健康狀態"""
    settings = get_settings()
    start_time = asyncio.get_event_loop().time()
    
    try:
        # 建立 Redis 連線
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # 測試連線
        redis_client.ping()
        
        # 測試基本操作
        test_key = "health_check_test"
        redis_client.set(test_key, "test", ex=10)
        redis_client.get(test_key)
        redis_client.delete(test_key)
        
        end_time = asyncio.get_event_loop().time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        logger.info(f"Redis 健康檢查成功，回應時間: {response_time}ms")
        return {
            "status": "healthy",
            "service": "redis",
            "response_time_ms": response_time,
            "message": "Redis 連線正常"
        }
        
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        error_msg = f"Redis 健康檢查失敗: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "unhealthy",
            "service": "redis",
            "response_time_ms": response_time,
            "message": error_msg,
            "error": str(e)
        }


async def check_minio_health() -> Dict[str, Any]:
    """檢查 MinIO 健康狀態"""
    settings = get_settings()
    start_time = asyncio.get_event_loop().time()
    
    try:
        # 檢查 MinIO 設定是否存在
        if not settings.MINIO_ENDPOINT:
            return {
                "status": "unhealthy",
                "service": "minio",
                "response_time_ms": 0,
                "message": "MinIO 設定未配置",
                "error": "MINIO_ENDPOINT 環境變數未設定"
            }
        
        # 建立 MinIO 客戶端
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        
        # 測試連線 - 嘗試列出桶
        list(minio_client.list_buckets())
        
        # 檢查主要桶是否存在
        bucket_name = settings.MINIO_BUCKET_NAME or "verification-documents"
        bucket_exists = minio_client.bucket_exists(bucket_name)
        
        end_time = asyncio.get_event_loop().time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        logger.info(f"MinIO 健康檢查成功，回應時間: {response_time}ms")
        return {
            "status": "healthy",
            "service": "minio",
            "response_time_ms": response_time,
            "message": f"MinIO 連線正常，桶 '{bucket_name}' 存在: {bucket_exists}",
            "bucket_exists": bucket_exists
        }
        
    except S3Error as e:
        end_time = asyncio.get_event_loop().time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        error_msg = f"MinIO S3 錯誤: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "unhealthy",
            "service": "minio",
            "response_time_ms": response_time,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        error_msg = f"MinIO 健康檢查失敗: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "unhealthy",
            "service": "minio",
            "response_time_ms": response_time,
            "message": error_msg,
            "error": str(e)
        }


async def check_all_services() -> Dict[str, Any]:
    """檢查所有服務的健康狀態"""
    logger.info("開始執行服務健康檢查...")
    
    # 並行執行所有健康檢查
    db_check_task = asyncio.create_task(check_database_health())
    redis_check_task = asyncio.create_task(check_redis_health())
    minio_check_task = asyncio.create_task(check_minio_health())
    
    # 等待所有檢查完成
    db_result, redis_result, minio_result = await asyncio.gather(
        db_check_task, redis_check_task, minio_check_task, return_exceptions=True
    )
    
    # 處理異常情況
    services = []
    for result, service_name in [
        (db_result, "database"),
        (redis_result, "redis"),
        (minio_result, "minio")
    ]:
        if isinstance(result, Exception):
            services.append({
                "status": "unhealthy",
                "service": service_name,
                "response_time_ms": 0,
                "message": f"{service_name} 健康檢查時發生異常",
                "error": str(result)
            })
        else:
            services.append(result)
    
    # 計算整體健康狀態
    healthy_services = [s for s in services if s["status"] == "healthy"]
    unhealthy_services = [s for s in services if s["status"] == "unhealthy"]
    
    overall_status = "healthy" if len(unhealthy_services) == 0 else "unhealthy"
    
    result = {
        "status": overall_status,
        "timestamp": asyncio.get_event_loop().time(),
        "services": services,
        "summary": {
            "total": len(services),
            "healthy": len(healthy_services),
            "unhealthy": len(unhealthy_services)
        }
    }
    
    if overall_status == "healthy":
        logger.info("所有服務健康檢查通過")
    else:
        logger.error(f"有 {len(unhealthy_services)} 個服務健康檢查失敗")
    
    return result


async def startup_health_check() -> None:
    """系統啟動時的健康檢查，如果失敗會拋出異常"""
    logger.info("執行系統啟動健康檢查...")
    
    health_result = await check_all_services()
    
    if health_result["status"] != "healthy":
        unhealthy_services = [
            s["service"] for s in health_result["services"] 
            if s["status"] == "unhealthy"
        ]
        error_msg = f"系統啟動失敗，以下服務不可用: {', '.join(unhealthy_services)}"
        logger.critical(error_msg)
        raise HealthCheckError(error_msg)
    
    logger.info("系統啟動健康檢查通過，所有服務運作正常")