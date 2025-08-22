import numpy as np
import librosa
import whisper
import torch
import os
import warnings
import gc

from sklearn.metrics.pairwise import cosine_similarity
from jiwer import wer
from pystoi import stoi
import parselmouth
import google.generativeai as genai

from src.shared.config.config import get_settings
from celery_app.services.model_manager import get_model_manager


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
def compute_hnr(path: str, time_step: float = 0.01) -> float:
    try:
        snd = parselmouth.Sound(path)
        hnr = snd.to_harmonicity_cc(time_step=time_step).get_mean()
        return float(hnr) if not np.isnan(hnr) else 0.0
    except Exception:
        return 0.0


def compute_clarity_metrics(path: str) -> dict:
    wav, sr = librosa.load(path, sr=16000, mono=True)
    noise_floor = np.percentile(np.abs(wav), 10)
    snr = 10 * np.log10(np.mean(wav**2) / (noise_floor**2 + 1e-6))
    hnr = compute_hnr(path)
    S = np.abs(np.fft.rfft(wav))
    entro = -np.sum((S / np.sum(S)) * np.log2(S / np.sum(S) + 1e-12))
    conf = whisper_confidence(path)
    stoiv = stoi(wav, wav, sr, extended=False)
    return {
        "snr": float(snr),
        "hnr": float(hnr),
        "entropy": float(entro),
        "conf": float(conf),
        "stoi": float(stoiv)
    }


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


def compute_similarity_metrics(path_ref: str, path_sam: str) -> dict:
    txt_r = whisper_transcribe(path_ref)
    txt_s = whisper_transcribe(path_sam)
    wer_sim = 1 - wer(txt_r, txt_s)

    mel_r = pad_or_trim_mel(
        whisper.log_mel_spectrogram(whisper.load_audio(path_ref))
    )
    mel_s = pad_or_trim_mel(
        whisper.log_mel_spectrogram(whisper.load_audio(path_sam))
    )

    model_manager = get_model_manager()
    with model_manager.use_model("small") as model:
        with torch.no_grad():
            e_r = model.encoder(
                torch.from_numpy(mel_r).unsqueeze(0).to(model.device)
            )
            e_s = model.encoder(
                torch.from_numpy(mel_s).unsqueeze(0).to(model.device)
            )
            
            emb_sim = embedding_cosine_similarity(
                e_r.mean(1).cpu().numpy()[0],
                e_s.mean(1).cpu().numpy()[0]
            )

    return {
        "emb": float(emb_sim),
        "wer": float(wer_sim),
        "txt_ref": txt_r,
        "txt_sam": txt_s
    }


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
    genai.configure(api_key=api_key)
    gm = genai.GenerativeModel("models/gemini-1.5-flash-latest")

    prompt = f"""
你是一位語音治療師，請依照以下結果提供 3–5 點可執行的發音／咬字練習建議：
1. Embed 相似度：{data['similarity']['emb']:.3f}；WER 相似度：{data['similarity']['wer']:.3f}
2. 參考音檔清晰度：SNR={data['clarity_ref']['snr']:.1f}, HNR={data['clarity_ref']['hnr']:.1f}
   待測音檔清晰度：SNR={data['clarity_sam']['snr']:.1f}, HNR={data['clarity_sam']['hnr']:.1f}
3. Composite Index={data['index']:.3f} → Level {data['level']}
"""
    reply = gm.generate_content(prompt)
    return reply.text.strip()


# ─── 主函式 ───
def compute_scores_and_feedback(path_ref: str, path_sam: str) -> dict:
    settings = get_settings()
    print("開始音訊分析...")
    
    # 執行分析
    sim = compute_similarity_metrics(path_ref, path_sam)
    ref_cl = compute_clarity_metrics(path_ref)
    sam_cl = compute_clarity_metrics(path_sam)
    idx = composite_index(ref_cl, sam_cl, sim)
    lvl = classify_level(idx)

    result = {
        "similarity": sim,
        "clarity_ref": ref_cl,
        "clarity_sam": sam_cl,
        "index": idx,
        "level": lvl
    }

    # 生成建議
    print("生成 AI 建議...")
    result["suggestions"] = generate_gemini_suggestion(result, settings.GEMINI_API_KEY)
    
    print("分析完成")
    return result