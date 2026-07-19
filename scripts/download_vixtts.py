"""Tải model viXTTS (XTTS fine-tune tiếng Việt) về voices/viXTTS/.

Chạy trong .venv:
    python scripts/download_vixtts.py

Tải ~1.8GB (lần đầu). Giấy phép: dựa trên XTTS (Coqui Public Model License,
phi thương mại) — dùng cá nhân OK, KHÔNG kèm file model khi đưa lên GitHub.
"""

from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "voices" / "viXTTS"
DEST.mkdir(parents=True, exist_ok=True)

print("Đang tải viXTTS (~1.8GB, lần đầu hơi lâu)...")
snapshot_download(repo_id="capleaf/viXTTS", local_dir=str(DEST))

print("\nXong. Nội dung thư mục voices/viXTTS/:")
for p in sorted(DEST.rglob("*")):
    if p.is_file():
        print(f"   {p.relative_to(DEST)}  ({p.stat().st_size // 1024} KB)")
