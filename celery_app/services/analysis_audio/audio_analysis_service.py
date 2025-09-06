import numpy as np
import librosa
import whisper
import torch
import os
import warnings
import gc
import re
import time
import logging
from difflib import SequenceMatcher

from sklearn.metrics.pairwise import cosine_similarity
from jiwer import wer
from pystoi import stoi
import parselmouth
import google.generativeai as genai

from src.shared.config.config import get_settings
from celery_app.services.model_manager import get_model_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── 模型管理 ───
def get_whisper_model(model_name: str = "small"):
    """取得 Whisper 模型，使用模型管理器"""
    model_manager = get_model_manager()
    return model_manager.get_whisper_model(model_name)




# ─── Whisper 基礎 ───
def load_audio(path: str, sr: int = 16000) -> np.ndarray:
    wav, _ = librosa.load(path, sr=sr, mono=True)
    return wav


def whisper_transcribe(path: str,
                       model_name: str = "small",
                       language: str = "zh") -> str:
    model_manager = get_model_manager()
    with model_manager.use_model(model_name) as model:
        result = model.transcribe(path, language=language)
        return result["text"].strip()


def whisper_confidence(path: str, model_name: str = "small") -> float:
    model_manager = get_model_manager()
    with model_manager.use_model(model_name) as model:
        res = model.transcribe(path)
    confs = [
        w["confidence"]
        for seg in res.get("segments", [])
        for w in seg.get("words", [])
        if "confidence" in w
    ]
    if not confs:
        for seg in res.get("segments", []):
            if "avg_logprob" in seg:
                confs.append(1 / (1 + np.exp(-seg["avg_logprob"])))
    return float(np.mean(confs)) if confs else 0.0


# ─── 音訊特徵 ───


def compute_clarity_metrics(path: str) -> dict:
    """計算清晰度指標 - 改進版本"""
    result = {"snr": 0, "hnr": 5.0, "entropy": 0, "conf": 0, "stoi": 0}
    
    try:
        # SNR 計算
        try:
            wav, sr = librosa.load(path, sr=16000, mono=True)
            noise_floor = np.percentile(np.abs(wav), 10)
            snr = 10 * np.log10(np.mean(wav**2) / (noise_floor**2 + 1e-6))
            result["snr"] = float(snr)
        except Exception as e:
            logger.error(f"SNR 計算錯誤: {e}")
        
        # HNR 計算 - 直接在這裡計算，不依賴外部函數
        try:
            sound = parselmouth.Sound(path)
            harmonicity = sound.to_harmonicity()
            values = harmonicity.values.flatten()
            valid_values = values[values != -200]
            valid_values = valid_values[~np.isnan(valid_values)]
            
            if len(valid_values) > 0:
                hnr_mean = float(np.mean(valid_values))
                if -50 <= hnr_mean <= 50:
                    result["hnr"] = hnr_mean
                else:
                    result["hnr"] = 5.0
            else:
                result["hnr"] = 5.0
        except Exception as e:
            logger.error(f"HNR 計算錯誤: {e}")
            result["hnr"] = 5.0
        
        # 頻譜熵
        try:
            wav, sr = librosa.load(path, sr=16000, mono=True)
            S = np.abs(np.fft.rfft(wav))
            S_norm = S / (np.sum(S) + 1e-12)
            entropy = -np.sum(S_norm * np.log2(S_norm + 1e-12))
            result["entropy"] = float(entropy)
        except Exception as e:
            logger.error(f"熵計算錯誤: {e}")
        
        # Whisper 信心度
        try:
            conf = whisper_confidence(path)
            result["conf"] = float(conf)
        except Exception as e:
            logger.error(f"信心度計算錯誤: {e}")
        
        # STOI
        try:
            wav, sr = librosa.load(path, sr=16000, mono=True)
            stoi_val = stoi(wav, wav, sr, extended=False)
            result["stoi"] = float(stoi_val)
        except Exception as e:
            logger.error(f"STOI 計算錯誤: {e}")
        
        # 調試輸出
        logger.info(f"清晰度指標 - SNR: {result['snr']:.2f}, HNR: {result['hnr']:.2f}, 信心度: {result['conf']:.3f}")
        
        return result
        
    except Exception as e:
        logger.error(f"清晰度計算整體錯誤 {path}: {e}")
        return result


# ─── 相似度 ───
def pad_or_trim_mel(mel: np.ndarray, L: int = 3000) -> np.ndarray:
    t = mel.shape[-1]
    if t > L:
        return mel[:, :L]
    if t < L:
        return np.pad(mel, ((0, 0), (0, L - t)), mode="constant")
    return mel


def embedding_cosine_similarity(e1: np.ndarray, e2: np.ndarray) -> float:
    sim = cosine_similarity(e1.reshape(1, -1), e2.reshape(1, -1))[0, 0]
    return float(sim)


def normalize_text(text: str) -> str:
    """正規化文字（移除標點、統一格式）"""
    # 只保留中文字符、英文字母和數字
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
    return cleaned.lower()


def compute_text_similarity_strict(text_ref: str, text_sam: str) -> float:
    """嚴格的文字相似度計算"""
    if "[" in text_ref or "[" in text_sam:  # 轉錄失敗
        return 0.0
    
    # 更保守的文字正規化 - 只移除標點符號
    clean_ref = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text_ref)
    clean_sam = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text_sam)
    
    if len(clean_ref) == 0 and len(clean_sam) == 0:
        return 1.0
    elif len(clean_ref) == 0 or len(clean_sam) == 0:
        return 0.0
    
    # 使用多種相似度計算方法，取最嚴格的結果
    
    # 方法1: 字符級相似度
    char_similarity = SequenceMatcher(None, clean_ref, clean_sam).ratio()
    
    # 方法2: 詞級相似度 (按字切分)
    ref_chars = list(clean_ref)
    sam_chars = list(clean_sam)
    word_similarity = SequenceMatcher(None, ref_chars, sam_chars).ratio()
    
    # 方法3: 編輯距離相似度
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    max_len = max(len(clean_ref), len(clean_sam))
    edit_distance = levenshtein_distance(clean_ref, clean_sam)
    edit_similarity = 1 - (edit_distance / max_len) if max_len > 0 else 0
    
    # 取最嚴格（最低）的相似度
    final_similarity = min(char_similarity, word_similarity, edit_similarity)
    
    logger.info(f"文字相似度詳細: 字符={char_similarity:.3f}, 詞級={word_similarity:.3f}, 編輯距離={edit_similarity:.3f}")
    logger.info(f"最終文字相似度: {final_similarity:.3f}")
    
    return float(final_similarity)


def compute_similarity_metrics(path_ref: str, path_sam: str) -> dict:
    """計算相似度指標"""
    try:
        # 轉錄
        txt_ref = whisper_transcribe(path_ref)
        txt_sam = whisper_transcribe(path_sam)
        
        logger.info(f"轉錄 - 參考: '{txt_ref}', 測試: '{txt_sam}'")
        
        # 使用嚴格的文字相似度計算
        wer_sim = compute_text_similarity_strict(txt_ref, txt_sam)
        
        # 音響相似度
        try:
            model_manager = get_model_manager()
            with model_manager.use_model("small") as model:
                mel_ref = pad_or_trim_mel(
                    whisper.log_mel_spectrogram(whisper.load_audio(path_ref))
                )
                mel_sam = pad_or_trim_mel(
                    whisper.log_mel_spectrogram(whisper.load_audio(path_sam))
                )
                
                with torch.no_grad():
                    # 計算 embeddings
                    emb_ref = model.encoder(torch.from_numpy(mel_ref).unsqueeze(0).to(model.device))
                    emb_sam = model.encoder(torch.from_numpy(mel_sam).unsqueeze(0).to(model.device))
                    
                    # 平均池化並計算相似度
                    emb_ref_mean = emb_ref.mean(dim=1).cpu().numpy()[0]
                    emb_sam_mean = emb_sam.mean(dim=1).cpu().numpy()[0]
                    
                    emb_sim = embedding_cosine_similarity(emb_ref_mean, emb_sam_mean)
        
        except Exception as e:
            logger.error(f"音響相似度計算錯誤: {e}")
            emb_sim = 0.0
        
        # 調整權重 - 提高文字相似度的重要性
        combined = 0.5 * emb_sim + 0.5 * wer_sim  # 改為 50/50 權重
        
        logger.info(f"相似度結果: 音響={emb_sim:.3f}, 文字={wer_sim:.3f}, 組合={combined:.3f}")
        
        return {
            "emb": float(combined),
            "wer": float(wer_sim),
            "txt_ref": txt_ref,
            "txt_sam": txt_sam
        }
        
    except Exception as e:
        logger.error(f"相似度計算錯誤: {e}")
        return {"emb": 0.0, "wer": 0.0, "txt_ref": "錯誤", "txt_sam": "錯誤"}


# ─── 分級 ───
def normalize_ratio(n: float, d: float) -> float:
    return float(np.clip(n / d, 0, 1)) if d > 0 else 0.0


def composite_index(ref: dict, sam: dict, sim: dict) -> float:
    ratios = [
        normalize_ratio(sam["snr"], ref["snr"]),
        normalize_ratio(sam["hnr"], ref["hnr"]),
        normalize_ratio(ref["entropy"], sam["entropy"]),
        normalize_ratio(sam["conf"], ref["conf"]),
        normalize_ratio(sam["stoi"], ref["stoi"]),
        sim["emb"],
        sim["wer"]
    ]
    W = np.array([0.15, 0.10, 0.15, 0.15, 0.15, 0.20, 0.10])
    return float(np.dot(ratios, W))


def classify_level(idx: float) -> int:
    if idx >= 0.85:
        return 1
    if idx >= 0.65:
        return 2
    if idx >= 0.45:
        return 3
    if idx >= 0.25:
        return 4
    return 5


# ─── Gemini 建議 ───
def generate_gemini_suggestion(data: dict, api_key: str) -> str:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

        level = data['level']
        sim = data['similarity']
        
        prompt = f"""
你是語音治療師，為 Level {level} 的患者提供建議。
參考發音：{sim['txt_ref']}
實際發音：{sim['txt_sam']}
音質相似度：{sim['emb']:.2f}
文字準確度：{sim['wer']:.2f}

請用溫暖鼓勵的語氣，提供 3-4 個實用的練習建議。
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"建議生成錯誤: {e}")
        level_msg = {
            1: "發音表現優秀！繼續保持練習。",
            2: "發音良好，可以針對細節微調。",
            3: "發音有進步空間，建議每天練習 10-15 分鐘。",
            4: "需要加強練習，建議從基本發音開始。",
            5: "建議尋求專業語音治療師協助。"
        }
        return level_msg.get(level, "請持續練習發音。")

    


# ─── 主函式 ───
def compute_scores_and_feedback(path_ref: str, path_sam: str) -> dict:
    """主要分析函數 - 改進版本"""
    try:
        settings = get_settings()
        logger.info("開始語音分析...")
        start_time = time.time()
        
        # 計算各項指標
        similarity = compute_similarity_metrics(path_ref, path_sam)
        ref_clarity = compute_clarity_metrics(path_ref)
        sam_clarity = compute_clarity_metrics(path_sam)
        
        # 綜合評估
        index = composite_index(ref_clarity, sam_clarity, similarity)
        
        # 強制修正邏輯：如果文字差異極大，直接降級
        if similarity["wer"] < 0.3:  # 文字相似度低於30%
            logger.info(f"檢測到文字相似度過低({similarity['wer']:.3f})，強制調整評級")
            index = min(index, 0.4)  # 強制不超過0.4
            
        if similarity["wer"] < 0.2:  # 文字相似度低於20%
            logger.info(f"文字相似度極低({similarity['wer']:.3f})，強制設為低級")
            index = min(index, 0.25)  # 強制Level 4或5
            
        level = classify_level(index)
        
        # 最後檢查：如果文字完全不匹配但還是高分，強制降級
        if similarity["wer"] < 0.25 and level <= 2:
            logger.info("文字差異過大但評級過高，強制降為Level 4")
            level = 4
            index = 0.35
        
        result = {
            "similarity": similarity,
            "clarity_ref": ref_clarity,
            "clarity_sam": sam_clarity,
            "index": index,
            "level": level,
            "analysis_time": time.time() - start_time
        }
        
        # 生成建議
        logger.info("生成 AI 建議...")
        result["suggestions"] = generate_gemini_suggestion(result, settings.GEMINI_API_KEY)
        
        logger.info(f"最終結果 - Level: {level}, Index: {index:.3f}, WER: {similarity['wer']:.3f}")
        logger.info(f"分析完成，耗時: {result['analysis_time']:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"分析失敗: {e}")
        return {
            "similarity": {"emb": 0.0, "wer": 0.0, "txt_ref": "錯誤", "txt_sam": "錯誤"},
            "clarity_ref": {"snr": 0, "hnr": 0, "entropy": 0, "conf": 0, "stoi": 0},
            "clarity_sam": {"snr": 0, "hnr": 0, "entropy": 0, "conf": 0, "stoi": 0},
            "index": 0.0,
            "level": 5,
            "suggestions": "系統分析失敗，請檢查音檔。",
            "error": str(e),
            "analysis_time": 0.0
        }