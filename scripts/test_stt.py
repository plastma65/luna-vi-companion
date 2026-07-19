"""Test STT: thu 5 giây tiếng nói rồi chuyển thành chữ (faster-whisper).

Chạy:
    python scripts/test_stt.py
"""

import sounddevice as sd
from faster_whisper import WhisperModel

SR = 16000
DURATION = 5

# Model: 'small' tải nhanh, đủ dùng. Muốn chính xác hơn đổi 'medium' (nặng hơn).
MODEL_SIZE = "small"
# GPU: nếu báo lỗi CUDA/cuDNN, đổi DEVICE="cpu" và COMPUTE="int8"
DEVICE = "cuda"
COMPUTE = "float16"

print(f"Đang tải model STT '{MODEL_SIZE}' ({DEVICE})... lần đầu hơi lâu.")
model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE)

input(f"\nNhấn Enter rồi nói tiếng Việt trong {DURATION} giây...")
print("🎤 Đang nghe...")
audio = sd.rec(int(DURATION * SR), samplerate=SR, channels=1, dtype="float32")
sd.wait()
audio = audio.flatten()

print("📝 Đang nhận dạng...")
segments, info = model.transcribe(audio, language="vi", beam_size=5)
text = " ".join(seg.text.strip() for seg in segments).strip()

print("\n=== Anh vừa nói ===")
print(text if text else "(không nghe rõ, anh thử nói to/gần mic hơn)")
