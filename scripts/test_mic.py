"""Test mic + loa: thu 4 giây rồi phát lại. Xác nhận phần cứng âm thanh OK.

Chạy:
    python scripts/test_mic.py
"""

import sounddevice as sd
import soundfile as sf

SR = 16000  # 16kHz — chuẩn cho nhận dạng giọng nói
DURATION = 4  # giây

print("=== Thiết bị âm thanh trên máy ===")
print(sd.query_devices())
print("\n(Nếu mic/loa không đúng, có thể chỉnh trong Windows Sound settings.)")

input(f"\nNhấn Enter rồi nói gì đó trong {DURATION} giây...")
print("🎤 Đang thu...")
audio = sd.rec(int(DURATION * SR), samplerate=SR, channels=1, dtype="float32")
sd.wait()

print("🔊 Đang phát lại...")
sd.play(audio, SR)
sd.wait()

sf.write("test_mic.wav", audio, SR)
print("\nĐã lưu test_mic.wav.")
print("Nếu anh vừa nghe lại được giọng mình => mic + loa OK, sang bước STT được rồi!")
