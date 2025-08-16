"""
AI 音訊分析任務

處理練習記錄的 AI 分析，包括發音準確度、流暢度等指標。
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

from ..app import app
from .utils import update_progress, log_task_start, log_task_complete, log_task_error
from ..services.analysis import compute_scores_and_feedback

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def analyze_test_audio_task(
    self, 
    practice_record_id: str, 
    analysis_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """AI 音訊分析測試任務
    
    流程
    - 1. 印出 `practice_record_id` 
    - 2. 從 celery_app/test/audio_sample 取得音檔
    - 3. 將兩個音檔丟入 `compute_scores_and_feedback` 函式進行分析
    - 4. 將分析回傳

    Args:
        self: Celery 任務實例
        practice_record_id: 練習記錄 ID
        analysis_params: 分析參數（目前未使用，預留擴展）
        
    Returns:
        result: 回傳分析結果

    Raises:
        ValueError: 當練習記錄不存在或音檔路徑無效時
        FileNotFoundError: 當音檔不存在時
        Exception: 音訊分析過程中的各種錯誤
    """
    task_id = self.request.id
    log_task_start("AI音訊分析測試任務", task_id)
    
    try:
        # 1. 印出練習記錄 ID
        print(f"開始處理練習記錄 ID: {practice_record_id}")
        
        # 2. 從 celery_app/test/audio_sample 取得音檔
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        audio_sample_dir = os.path.join(current_dir, "test", "audio_sample")
        
        # 取得測試音檔路徑
        example_audio = os.path.join(audio_sample_dir, "Example.mp3")
        patient_audio = os.path.join(audio_sample_dir, "Patient.mp3")
        
        # 檢查音檔是否存在
        if not os.path.exists(example_audio):
            raise FileNotFoundError(f"範例音檔不存在: {example_audio}")
        if not os.path.exists(patient_audio):
            raise FileNotFoundError(f"病患音檔不存在: {patient_audio}")
            
        # print(f"使用範例音檔: {example_audio}")
        # print(f"使用病患音檔: {patient_audio}")
        
        # 更新任務進度
        update_progress("音檔載入完成，開始分析", 30)
        
        # 3. 將兩個音檔丟入 compute_scores_and_feedback 函式進行分析
        # print("開始進行 AI 音訊分析...")
        analysis_result = compute_scores_and_feedback(
            path_ref=example_audio,
            path_sam=patient_audio
        )
        
        # 更新任務進度
        update_progress("分析完成，準備回傳結果", 80)
        
        # 4. 將分析回傳
        result = {
            "practice_record_id": practice_record_id,
            "analysis_result": analysis_result,
            "processed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        # print(f"分析完成，結果: {result}")
        
        # 更新任務進度
        update_progress("任務完成", 100)
        log_task_complete("AI音訊分析測試任務完成", task_id)
        
        return result
        
    except FileNotFoundError as e:
        error_msg = f"音檔不存在: {str(e)}"
        print(f"錯誤: {error_msg}")
        log_task_error("AI音訊分析測試任務", task_id, Exception(error_msg))
        raise ValueError(error_msg)
        
    except Exception as e:
        error_msg = f"AI 音訊分析過程中發生錯誤: {str(e)}"
        print(f"錯誤: {error_msg}")
        log_task_error("AI音訊分析測試任務", task_id, e)
        raise
   