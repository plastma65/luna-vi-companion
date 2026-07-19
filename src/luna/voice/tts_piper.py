"""TTS bằng piper — chạy TRONG tiến trình Luna (không cần server riêng).

- Nhẹ, nhanh, không xung đột thư viện.
- Đọc số tiếng Việt ("1" -> "một"), bỏ emoji, chỉnh tốc độ/cao độ.

Cài (trong .venv chính):  pip install piper-tts
Giọng: voices/vi_VN-vais1000-medium.onnx (chạy scripts/download_voice.py nếu thiếu).
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import sounddevice as sd

# ===== 2 núm chỉnh giọng (độc lập nhau) =====
# SPEED: tốc độ đọc.  1.0 = gốc, >1 nhanh hơn, <1 chậm hơn.
# PITCH: cao độ giọng. 1.0 = gốc, >1 trẻ/cao hơn, <1 trầm/lớn tuổi hơn.
# Chỉnh mỗi lần ~0.05 rồi nghe thử. Gợi ý: SPEED 1.05-1.25, PITCH 1.05-1.18.
SPEED = 0.7
PITCH = 1.4
# ============================================

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "voices" / "vi_VN-vais1000-medium.onnx"

_voice = None

_EMOJI = re.compile("[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff" "←-⇿⬀-⯿️]")

# ---- đọc số tiếng Việt ----
_ONES = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
_GROUP = ["", " nghìn", " triệu", " tỷ"]


def _doc_3(n: int, full: bool) -> str:
    tr, ch, dv = n // 100, (n % 100) // 10, n % 10
    parts = []
    if tr > 0 or full:
        parts.append(_ONES[tr] + " trăm")
    if ch == 0:
        if dv > 0:
            parts.append(("lẻ " if (tr > 0 or full) else "") + _ONES[dv])
    elif ch == 1:
        parts.append("mười")
        if dv == 1:
            parts.append("một")
        elif dv == 5:
            parts.append("lăm")
        elif dv > 0:
            parts.append(_ONES[dv])
    else:
        parts.append(_ONES[ch] + " mươi")
        if dv == 1:
            parts.append("mốt")
        elif dv == 5:
            parts.append("lăm")
        elif dv > 0:
            parts.append(_ONES[dv])
    return " ".join(parts)


def _doc_so(n: int) -> str:
    if n == 0:
        return "không"
    groups = []
    while n > 0:
        groups.append(n % 1000)
        n //= 1000
    if len(groups) > 4:
        return " ".join(_ONES[int(c)] for c in str(n))
    out, top = [], len(groups) - 1
    for i in range(top, -1, -1):
        if groups[i] == 0:
            continue
        out.append(_doc_3(groups[i], full=(i != top)) + _GROUP[i])
    return " ".join(out).strip()


def _normalize(text: str) -> str:
    text = _EMOJI.sub("", text)
    text = text.replace("%", " phần trăm")
    text = re.sub(r"\d+", lambda m: _doc_so(int(m.group(0))), text)
    return text.strip()


def _get_voice():
    global _voice
    if _voice is None:
        from piper import PiperVoice

        _voice = PiperVoice.load(str(MODEL))
    return _voice


def speak(text: str) -> None:
    """Đọc câu tiếng Việt qua loa (chặn tới khi đọc xong)."""
    text = _normalize(text)
    if not text:
        return
    voice = _get_voice()

    # Tách 2 núm: phát ở sr*PITCH nâng cao độ (nhưng cũng làm nhanh lên),
    # nên bù lại bằng length_scale = PITCH/SPEED để tốc độ đọc đúng bằng SPEED.
    # -> Kết quả: cao độ = PITCH, tốc độ = SPEED, không dính vào nhau.
    length_scale = max(0.5, PITCH / SPEED)
    syn = None
    try:
        from piper import SynthesisConfig

        syn = SynthesisConfig(length_scale=length_scale)
    except Exception:  # noqa: BLE001
        pass

    parts, sr = [], 30000
    gen = voice.synthesize(text, syn_config=syn) if syn else voice.synthesize(text)
    for chunk in gen:
        sr = getattr(chunk, "sample_rate", sr)
        if hasattr(chunk, "audio_float_array"):
            parts.append(np.asarray(chunk.audio_float_array, dtype=np.float32))
        elif hasattr(chunk, "audio_int16_array"):
            parts.append(np.asarray(chunk.audio_int16_array, dtype=np.float32) / 32768.0)
        else:
            b = chunk.audio_int16_bytes
            parts.append(np.frombuffer(b, dtype=np.int16).astype(np.float32) / 32768.0)

    if not parts:
        return
    audio = np.concatenate(parts)
    sd.play(audio, int(sr * PITCH))  # phát ở sr cao hơn -> nâng cao độ (trẻ hơn)
    sd.wait()


if __name__ == "__main__":
    # Nghe thử nhanh để chỉnh SPEED/PITCH (không cần nạp cả Luna):
    #   python -m luna.voice.tts_piper
    #   python -m luna.voice.tts_piper "Câu anh muốn nghe thử"
    import sys

    demo = " ".join(sys.argv[1:]) or "Dạ, em là Luna. Anh nghe giọng em thế này ổn chưa ạ?"
    print(f"SPEED={SPEED}  PITCH={PITCH}")
    print(f"Đọc thử: {demo}")
    speak(demo)
