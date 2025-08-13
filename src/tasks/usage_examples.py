"""
VocalBorn Celery 任務使用範例

這個檔案展示如何在 VocalBorn 專案中使用 Celery 任務系統，
包括任務提交、狀態查詢、結果獲取等常見操作。
"""

import asyncio
import time
from typing import Dict, Any, Optional
from uuid import uuid4

from .celery_app import app, monitor
from .celery_tasks import analyze_audio_task, test_task, health_check


class TaskManager:
    """任務管理器，提供高層級的任務操作介面"""
    
    def __init__(self):
        """初始化任務管理器"""
        self.celery_app = app
    
    async def submit_audio_analysis(
        self, 
        practice_record_id: str, 
        analysis_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """提交音訊分析任務
        
        Args:
            practice_record_id: 練習記錄 ID
            analysis_params: 分析參數
            
        Returns:
            任務 ID
        """
        # 使用 apply_async 方法提交任務到指定佇列
        task = analyze_audio_task.apply_async(
            args=[practice_record_id, analysis_params],
            queue='ai_analysis',
            routing_key='ai_analysis'
        )
        
        print(f"已提交音訊分析任務，任務 ID: {task.id}")
        print(f"練習記錄 ID: {practice_record_id}")
        
        return task.id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """獲取任務狀態
        
        Args:
            task_id: 任務 ID
            
        Returns:
            任務狀態資訊
        """
        result = self.celery_app.AsyncResult(task_id)
        
        try:
            status_info = {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "failed": result.failed() if result.ready() else None,
            }
            
            # 如果任務正在執行，獲取進度資訊
            if result.status == 'PROGRESS':
                try:
                    status_info["progress"] = result.info
                except Exception:
                    status_info["progress"] = None
            
            # 如果任務完成，獲取結果
            elif result.ready():
                try:
                    if result.successful():
                        status_info["result"] = result.result
                    else:
                        # 安全獲取錯誤資訊
                        try:
                            status_info["error"] = str(result.info)
                        except Exception:
                            status_info["error"] = "任務執行失敗但無法獲取詳細錯誤資訊"
                except Exception as exc:
                    status_info["error"] = f"獲取任務結果時發生錯誤: {exc}"
        
        except Exception as exc:
            # 如果獲取狀態時發生錯誤，返回基本資訊
            status_info = {
                "task_id": task_id,
                "status": "UNKNOWN",
                "ready": False,
                "successful": None,
                "failed": None,
                "error": f"獲取任務狀態時發生錯誤: {exc}"
            }
        
        return status_info
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任務
        
        Args:
            task_id: 任務 ID
            
        Returns:
            是否成功取消
        """
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            print(f"已取消任務: {task_id}")
            return True
        except Exception as exc:
            print(f"取消任務失敗: {exc}")
            return False
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """獲取 Worker 統計資訊"""
        return monitor.get_worker_stats()
    
    def get_queue_length(self, queue_name: str = "ai_analysis") -> int:
        """獲取佇列長度"""
        return monitor.get_queue_length(queue_name)


def example_basic_usage():
    """基本使用範例"""
    print("=== VocalBorn Celery 基本使用範例 ===")
    
    # 建立任務管理器
    task_manager = TaskManager()
    
    # 1. 提交測試任務
    print("\n1. 提交測試任務")
    test_result = test_task.apply_async(
        args=["這是一個測試訊息"],
        queue='ai_analysis'
    )
    print(f"測試任務 ID: {test_result.id}")
    
    # 2. 查詢任務狀態
    print("\n2. 查詢任務狀態")
    status = task_manager.get_task_status(test_result.id)
    print(f"任務狀態: {status}")
    
    # 3. 等待任務完成並獲取結果
    print("\n3. 等待任務完成")
    try:
        result = test_result.get(timeout=30)  # 等待 30 秒
        print(f"任務結果: {result}")
    except Exception as exc:
        print(f"任務執行失敗: {exc}")
    
    # 4. 提交音訊分析任務（模擬）
    print("\n4. 提交音訊分析任務")
    practice_record_id = str(uuid4())
    analysis_params = {
        "analysis_type": "full",
        "include_suggestions": True,
        "model_version": "v2.1"
    }
    
    analysis_task_id = asyncio.run(
        task_manager.submit_audio_analysis(practice_record_id, analysis_params)
    )
    print(f"音訊分析任務已提交: {analysis_task_id}")


def example_monitoring():
    """監控使用範例"""
    print("\n=== VocalBorn Celery 監控範例 ===")
    
    task_manager = TaskManager()
    
    # 1. 基本功能測試
    print("\n1. 任務管理器狀態")
    print(f"Celery 應用: {task_manager.celery_app.main}")
    
    # 2. 提交測試任務
    print("\n2. 提交測試任務")
    test_result = test_task.apply_async(
        args=["監控測試訊息"],
        queue='ai_analysis'
    )
    print(f"測試任務 ID: {test_result.id}")
    
    # 3. 查詢任務狀態
    print("\n3. 查詢任務狀態")
    status = task_manager.get_task_status(test_result.id)
    print(f"任務狀態: {status['status']}")
    
    # 4. 等待測試任務完成
    print("\n4. 等待任務完成")
    try:
        result = test_result.get(timeout=15)
        print(f"任務結果: {result}")
    except Exception as exc:
        print(f"任務執行超時或失敗: {exc}")
    
    print("\n監控功能測試完成")


def example_error_handling():
    """錯誤處理範例"""
    print("\n=== VocalBorn Celery 錯誤處理範例 ===")
    
    task_manager = TaskManager()
    
    # 1. 測試任務狀態查詢錯誤處理
    print("\n1. 測試無效任務 ID 查詢")
    invalid_task_id = "invalid-task-id-123"
    status = task_manager.get_task_status(invalid_task_id)
    print(f"無效任務查詢結果: {status}")
    
    # 2. 取消任務範例
    print("\n2. 取消任務範例")
    cancel_task = test_task.apply_async(
        args=["這個任務將被取消"],
        queue='ai_analysis'
    )
    print(f"提交任務: {cancel_task.id}")
    
    # 查詢任務狀態
    status = task_manager.get_task_status(cancel_task.id)
    print(f"任務狀態: {status['status']}")
    
    # 立即取消任務
    success = task_manager.cancel_task(cancel_task.id)
    print(f"任務取消{'成功' if success else '失敗'}")
    
    # 再次查詢狀態
    time.sleep(1)
    final_status = task_manager.get_task_status(cancel_task.id)
    print(f"取消後狀態: {final_status['status']}")
    
    print("\n錯誤處理測試完成")


def example_batch_processing():
    """批次處理範例"""
    print("\n=== VocalBorn Celery 批次處理範例 ===")
    
    # 1. 批次提交多個任務
    print("\n1. 批次提交任務")
    task_ids = []
    
    for i in range(5):
        practice_record_id = str(uuid4())
        task = analyze_audio_task.apply_async(
            args=[practice_record_id, {"batch_id": i}],
            queue='ai_analysis'
        )
        task_ids.append(task.id)
        print(f"已提交任務 {i+1}: {task.id}")
    
    # 2. 監控批次任務進度
    print("\n2. 監控批次任務進度")
    task_manager = TaskManager()
    
    completed_count = 0
    while completed_count < len(task_ids):
        completed_count = 0
        for task_id in task_ids:
            status = task_manager.get_task_status(task_id)
            if status['ready']:
                completed_count += 1
        
        print(f"已完成 {completed_count}/{len(task_ids)} 個任務")
        
        if completed_count < len(task_ids):
            time.sleep(2)
    
    print("所有批次任務已完成")


if __name__ == "__main__":
    """執行所有範例"""
    print("VocalBorn Celery 任務系統使用範例")
    print("=" * 50)
    
    try:
        # 基本使用範例
        example_basic_usage()
        
        # 監控範例
        example_monitoring()
        
        # 錯誤處理範例
        example_error_handling()
        
        # 批次處理範例
        # example_batch_processing()  # 註解掉以避免產生太多任務
        
    except Exception as exc:
        print(f"範例執行失敗: {exc}")
        import traceback
        traceback.print_exc()