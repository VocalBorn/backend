"""
測試任務

用於驗證 Celery 配置是否正確，以及測試任務執行流程。
"""

import time
from typing import Dict, Any
from datetime import datetime

from ..app import app
from .utils import update_progress, log_task_start, log_task_complete


@app.task(bind=True)
def test_task(self, message: str = "Hello from Celery!") -> Dict[str, Any]:
    """測試任務
    
    Args:
        self: Celery 任務實例
        message: 測試訊息
        
    Returns:
        測試結果字典
    """
    task_id = self.request.id
    log_task_start("測試任務", task_id, message=message)
    
    # 模擬處理過程，展示進度更新
    for i in range(5):
        step_name = f'處理步驟 {i+1}'
        progress = (i + 1) * 20
        update_progress(step_name, progress, message=message)
        time.sleep(5)  # 模擬處理時間
    
    result = {
        "task_id": task_id,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "steps_completed": 5
    }
    
    log_task_complete("測試任務", task_id, result)
    return result