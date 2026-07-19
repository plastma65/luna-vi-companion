"""Test TTS: chữ -> giọng Luna qua loa (piper), có chỉnh tốc độ & độ trẻ.

Chạy:
    python scripts/test_tts.py

Anh vặn 2 núm dưới đây theo tai:
- SPEED  : >1 = nói CHẬM/điềm hơn (1.18 chậm rãi). <1 = nhanh hơn.
- PITCH  : <1 = giọng TRẦM/ấm hơn (0.95 trầm nhẹ, kiểu đàn chị). >1 = trẻ/cao. 1.0 = gốc.
"""

from pathlib import Path

import numpy as np
import sounddevice as sd
from piper import PiperVoice

# ===== 2 núm để anh chỉnh =====
SPEED = 1.18  # chậm rãi, điềm đạm
PITCH = 0.95  # trầm & ấm hơn (kiểu đàn chị đại học)
# ==============================

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "voices" / "vi_VN-vais1000-medium.onnx"

print("Đang nạp giọng Luna...")
voice = PiperVoice.load(str(MODEL))

# length_scale điều khiển tốc độ đọc; nhân thêm PITCH để bù cho việc phát nhanh hơn
syn_config = None
try:
    from piper import SynthesisConfig

    syn_config = SynthesisConfig(length_scale=SPEED * PITCH)
except Exception:
    print("(Bản piper này không có SynthesisConfig, chỉ chỉnh được cao độ.)")

text = "Dạ em chào anh, em là Luna, người bạn đồng hành của anh đây ạ."
print("Đang tổng hợp giọng nói...")

parts = []
sr = 22050
gen = voice.synthesize(text, syn_config=syn_config) if syn_config else voice.synthesize(text)
for chunk in gen:
    sr = getattr(chunk, "sample_rate", sr)
    if hasattr(chunk, "audio_float_array"):
        parts.append(np.asarray(chunk.audio_float_array, dtype=np.float32))
    elif hasattr(chunk, "audio_int16_array"):
        parts.append(np.asarray(chunk.audio_int16_array, dtype=np.float32) / 32768.0)
    else:
        b = chunk.audio_int16_bytes
        parts.append(np.frombuffer(b, dtype=np.int16).astype(np.float32) / 32768.0)

audio = np.concatenate(parts)

# Phát ở sample-rate cao hơn -> nâng cao độ (trẻ hơn). SPEED đã bù nên tốc độ giữ nguyên.
play_sr = int(sr * PITCH)
print(f"🔊 Đang phát giọng Luna... (SPEED={SPEED}, PITCH={PITCH})")
sd.play(audio, play_sr)
sd.wait()
print("Xong. Anh nghe ổn chưa? Chỉnh SPEED/PITCH ở đầu file rồi chạy lại để tinh chỉnh.")
