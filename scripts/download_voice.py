"""Tải giọng nữ tiếng Việt cho piper (VAIS-1000, medium).

Chạy:
    python scripts/download_voice.py

Tải 2 file (.onnx + .onnx.json) vào thư mục voices/. Chỉ dùng thư viện chuẩn.
"""

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOICE_DIR = ROOT / "voices"
VOICE_DIR.mkdir(exist_ok=True)

BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vais1000/medium/"
FILES = ["vi_VN-vais1000-medium.onnx", "vi_VN-vais1000-medium.onnx.json"]

for f in FILES:
    dest = VOICE_DIR / f
    if dest.exists():
        print("Đã có sẵn:", f)
        continue
    print("Đang tải:", f, "...")
    urllib.request.urlretrieve(BASE + f, dest)
    print("  xong ->", dest)

print("\nHoàn tất. Giọng Luna nằm ở:", VOICE_DIR)
