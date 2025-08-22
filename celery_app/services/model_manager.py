"""AI 模型管理器
提供智能的模型載入、快取和生命週期管理功能。
"""

import gc
import logging
import threading
import time
import weakref
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set
import psutil
import torch
import whisper

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """模型資訊"""
    name: str
    model: Any
    device: str
    last_used: float = field(default_factory=time.time)
    memory_size: int = 0
    reference_count: int = 0


class ModelManager:
    """AI 模型管理器
    
    提供以下功能：
    - 線程安全的模型載入和快取
    - 自動記憶體管理和清理
    - GPU/CPU 智能分配
    - 模型預熱和生命週期管理
    """
    
    def __init__(self, 
                 max_memory_gb: float = 4.0,
                 cleanup_interval: int = 300,
                 max_idle_time: int = 1800):
        """初始化模型管理器
        
        Args:
            max_memory_gb: 最大記憶體使用量（GB）
            cleanup_interval: 清理檢查間隔（秒）
            max_idle_time: 模型最大閒置時間（秒）
        """
        self._models: Dict[str, ModelInfo] = {}
        self._lock = threading.RLock()
        self._max_memory_bytes = int(max_memory_gb * 1024 * 1024 * 1024)
        self._cleanup_interval = cleanup_interval
        self._max_idle_time = max_idle_time
        self._last_cleanup = time.time()
        self._active_models: Set[str] = set()
        
        # 檢測可用設備
        self._device = self._detect_device()
        logger.info(f"ModelManager 初始化完成，使用設備: {self._device}")
    
    def _detect_device(self) -> str:
        """檢測最佳可用設備"""
        # 只有 CUDA 可用時才使用 CUDA，其餘情況一律使用 CPU
        if torch.cuda.is_available():
            try:
                device = f"cuda:{torch.cuda.current_device()}"
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                logger.info(f"檢測到 CUDA 設備: {device}, 記憶體: {gpu_memory / 1024**3:.1f}GB")
                return device
            except Exception as e:
                logger.warning(f"CUDA 設備初始化失敗，回退到 CPU: {e}")
                return "cpu"
        else:
            # 無論是 MPS 還是其他設備，一律使用 CPU 以確保兼容性
            if torch.backends.mps.is_available():
                logger.info("檢測到 MPS 設備，但為確保穩定性使用 CPU")
            else:
                logger.info("未檢測到 CUDA 設備，使用 CPU")
            return "cpu"
    
    def get_whisper_model(self, model_name: str = "small") -> Any:
        """取得 Whisper 模型實例
        
        Args:
            model_name: 模型名稱 (tiny, base, small, medium, large)
            
        Returns:
            Whisper 模型實例
        """
        model_key = f"whisper_{model_name}"
        
        with self._lock:
            # 檢查快取中是否存在
            if model_key in self._models:
                model_info = self._models[model_key]
                model_info.last_used = time.time()
                model_info.reference_count += 1
                self._active_models.add(model_key)
                
                logger.debug(f"從快取載入 Whisper 模型: {model_name}")
                return model_info.model
            
            # 執行清理檢查
            self._cleanup_if_needed()
            
            # 載入新模型
            return self._load_whisper_model(model_name, model_key)
    
    def _load_whisper_model(self, model_name: str, model_key: str) -> Any:
        """載入 Whisper 模型"""
        logger.info(f"開始載入 Whisper 模型: {model_name}")
        start_time = time.time()
        
        try:
            # 檢查記憶體是否足夠
            if not self._check_memory_availability():
                self._force_cleanup()
            
            # 嘗試載入模型
            device_to_use = self._device
            
            try:
                # 首先嘗試指定設備
                model = whisper.load_model(model_name, device=device_to_use)
            except Exception as device_error:
                # 如果不是 CPU，嘗試回退到 CPU
                if device_to_use != "cpu":
                    logger.warning(f"設備 {device_to_use} 載入失敗，回退到 CPU: {device_error}")
                    device_to_use = "cpu"
                    model = whisper.load_model(model_name, device=device_to_use)
                else:
                    raise device_error
            
            # 計算模型大小
            model_size = self._estimate_model_size(model)
            
            # 儲存到快取
            model_info = ModelInfo(
                name=model_name,
                model=model,
                device=device_to_use,
                memory_size=model_size,
                reference_count=1
            )
            
            self._models[model_key] = model_info
            self._active_models.add(model_key)
            
            load_time = time.time() - start_time
            logger.info(f"Whisper 模型載入完成: {model_name}, "
                       f"耗時: {load_time:.2f}s, "
                       f"大小: {model_size / 1024**2:.1f}MB, "
                       f"設備: {device_to_use}")
            
            return model
            
        except Exception as e:
            logger.error(f"載入 Whisper 模型失敗: {model_name}, 錯誤: {e}")
            raise
    
    @contextmanager
    def use_model(self, model_name: str = "small"):
        """模型使用上下文管理器
        
        確保模型使用完畢後正確釋放引用
        
        Args:
            model_name: 模型名稱
            
        Yields:
            模型實例
        """
        model = self.get_whisper_model(model_name)
        try:
            yield model
        finally:
            self.release_model_reference(f"whisper_{model_name}")
    
    def release_model_reference(self, model_key: str) -> None:
        """釋放模型引用"""
        with self._lock:
            if model_key in self._models:
                model_info = self._models[model_key]
                model_info.reference_count = max(0, model_info.reference_count - 1)
                
                if model_info.reference_count == 0:
                    self._active_models.discard(model_key)
    
    def _estimate_model_size(self, model: Any) -> int:
        """估算模型記憶體大小"""
        if hasattr(model, 'parameters'):
            total_params = sum(p.numel() for p in model.parameters())
            # 假設每個參數 4 bytes (float32)
            return total_params * 4
        return 0
    
    def _check_memory_availability(self) -> bool:
        """檢查記憶體可用性"""
        try:
            # 檢查系統記憶體
            memory = psutil.virtual_memory()
            available_memory = memory.available
            
            # 檢查 GPU 記憶體（如果使用 CUDA）
            if self._device.startswith("cuda"):
                gpu_memory = torch.cuda.memory_reserved() + torch.cuda.memory_allocated()
                total_gpu_memory = torch.cuda.get_device_properties(0).total_memory
                gpu_usage_ratio = gpu_memory / total_gpu_memory
                
                if gpu_usage_ratio > 0.8:  # GPU 使用率超過 80%
                    logger.warning(f"GPU 記憶體使用率過高: {gpu_usage_ratio:.1%}")
                    return False
            
            # 檢查是否超過設定的記憶體限制
            current_usage = sum(info.memory_size for info in self._models.values())
            if current_usage > self._max_memory_bytes:
                logger.warning(f"模型記憶體使用量超過限制: {current_usage / 1024**3:.1f}GB")
                return False
            
            return available_memory > 1024 * 1024 * 1024  # 至少需要 1GB 可用記憶體
            
        except Exception as e:
            logger.warning(f"記憶體檢查失敗: {e}")
            return True  # 檢查失敗時允許載入
    
    def _cleanup_if_needed(self) -> None:
        """根據需要執行清理"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_unused_models()
            self._last_cleanup = current_time
    
    def _cleanup_unused_models(self) -> None:
        """清理未使用的模型"""
        current_time = time.time()
        models_to_remove = []
        
        for model_key, model_info in self._models.items():
            # 跳過正在使用的模型
            if model_key in self._active_models and model_info.reference_count > 0:
                continue
            
            # 檢查是否超過閒置時間
            idle_time = current_time - model_info.last_used
            if idle_time > self._max_idle_time:
                models_to_remove.append(model_key)
        
        # 移除閒置模型
        for model_key in models_to_remove:
            self._remove_model(model_key)
        
        if models_to_remove:
            logger.info(f"清理了 {len(models_to_remove)} 個閒置模型")
    
    def _force_cleanup(self) -> None:
        """強制清理記憶體"""
        logger.warning("執行強制記憶體清理")
        
        # 移除所有非活躍模型
        models_to_remove = [
            key for key, info in self._models.items()
            if key not in self._active_models or info.reference_count == 0
        ]
        
        for model_key in models_to_remove:
            self._remove_model(model_key)
        
        # 執行垃圾回收
        gc.collect()
        
        # 清理 GPU 快取（如果使用 CUDA）
        if self._device.startswith("cuda"):
            torch.cuda.empty_cache()
        
        logger.info(f"強制清理完成，釋放了 {len(models_to_remove)} 個模型")
    
    def _remove_model(self, model_key: str) -> None:
        """移除模型"""
        if model_key in self._models:
            model_info = self._models[model_key]
            
            # 清理模型
            del model_info.model
            del self._models[model_key]
            self._active_models.discard(model_key)
            
            logger.debug(f"已移除模型: {model_key}")
    
    def preload_models(self, model_names: list = None) -> None:
        """預載入常用模型
        
        Args:
            model_names: 要預載入的模型名稱列表
        """
        if model_names is None:
            model_names = ["small"]  # 預設載入 small 模型
        
        logger.info(f"開始預載入模型: {model_names}")
        
        for model_name in model_names:
            try:
                with self.use_model(model_name):
                    logger.info(f"預載入模型完成: {model_name}")
            except Exception as e:
                logger.error(f"預載入模型失敗: {model_name}, 錯誤: {e}")
    
    def get_status(self) -> dict:
        """取得模型管理器狀態"""
        with self._lock:
            total_memory = sum(info.memory_size for info in self._models.values())
            active_count = len(self._active_models)
            
            models_info = {}
            for key, info in self._models.items():
                models_info[key] = {
                    'name': info.name,
                    'device': info.device,
                    'memory_mb': info.memory_size / 1024**2,
                    'last_used': info.last_used,
                    'reference_count': info.reference_count,
                    'is_active': key in self._active_models
                }
            
            return {
                'device': self._device,
                'total_models': len(self._models),
                'active_models': active_count,
                'total_memory_mb': total_memory / 1024**2,
                'max_memory_mb': self._max_memory_bytes / 1024**2,
                'models': models_info
            }
    
    def cleanup_all(self) -> None:
        """清理所有模型"""
        logger.info("清理所有模型")
        
        with self._lock:
            model_keys = list(self._models.keys())
            for model_key in model_keys:
                self._remove_model(model_key)
            
            self._active_models.clear()
        
        gc.collect()
        if self._device.startswith("cuda"):
            torch.cuda.empty_cache()
        
        logger.info("所有模型已清理完成")


# 全域模型管理器實例
_global_model_manager: Optional[ModelManager] = None
_manager_lock = threading.Lock()


def get_model_manager() -> ModelManager:
    """取得全域模型管理器實例（單例模式）"""
    global _global_model_manager
    
    if _global_model_manager is None:
        with _manager_lock:
            if _global_model_manager is None:
                _global_model_manager = ModelManager()
    
    return _global_model_manager


def preload_common_models():
    """預載入常用模型（在 worker 啟動時呼叫）"""
    manager = get_model_manager()
    manager.preload_models(["small"])


def cleanup_models():
    """清理所有模型（在 worker 關閉時呼叫）"""
    global _global_model_manager
    
    if _global_model_manager is not None:
        _global_model_manager.cleanup_all()
        _global_model_manager = None


__all__ = [
    "ModelManager",
    "get_model_manager", 
    "preload_common_models",
    "cleanup_models"
]