import streamlit as st
import edge_tts
import asyncio
import os

st.title("台灣中文 文字轉語音（Edge TTS） Demo")

text = st.text_area("請輸入要轉語音的內容：", "今天天氣真好，我想去公園散步。", height=100)

# 語者選擇
voice = st.selectbox(
    "選擇語者",
    [
        "zh-TW-HsiaoChenNeural",  # 女聲
        "zh-TW-YunJheNeural"      # 男聲
    ]
)
# 語速與音調調整
rate = st.slider("語速調整 (%)", -50, 50, 0)
pitch = st.slider("音調調整 (Hz)", -20, 20, 0)

output_file = "tts_output.mp3"

def get_rate_str(rate):
    return f"{'+' if rate >= 0 else ''}{rate}%"

def get_pitch_str(pitch):
    return f"{'+' if pitch >= 0 else ''}{pitch}Hz"

async def tts_edge(text, output_file, voice, rate, pitch):
    communicate = edge_tts.Communicate(
        text,
        voice=voice,
        rate=get_rate_str(rate),
        pitch=get_pitch_str(pitch)
    )
    await communicate.save(output_file)

if st.button("產生語音"):
    asyncio.run(tts_edge(text, output_file, voice, rate, pitch))
    st.success("語音檔案已產生！")
    audio_bytes = open(output_file, "rb").read()
    st.audio(audio_bytes, format="audio/mp3")
    os.remove(output_file)

st.info("edge-tts 支援台灣腔男女聲、語速與音調調整，品質佳。\n如遇網路問題請稍後再試。")
