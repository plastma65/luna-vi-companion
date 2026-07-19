"""TTS viXTTS chạy TRONG tiến trình Luna — chất giọng đẹp như bản server,
nhưng KHÔNG cần chạy server HTTP riêng.

- Nạp model 1 lần (lazy: chỉ nạp khi nói câu đầu, ~20-40s), sau đó nhanh.
- Giữ nguyên cấu hình giọng đã tinh chỉnh ở bản server cũ.
- Bỏ emoji, đọc số tiếng Việt ("1" -> "một").

Yêu cầu: coqui-tts cài trong .venv chính, model ở voices/viXTTS/.
    pip install coqui-tts
"""

from __future__ import annotations

import os

os.environ["COQUI_TOS_AGREED"] = "1"  # tự đồng ý giấy phép model (dùng cá nhân)

import re
import types
from pathlib import Path

import numpy as np
import sounddevice as sd

# ===== 2 núm chỉnh giọng (giống bản server cũ) =====
# Giọng mẫu trong voices/viXTTS/samples/:
#   nu-luu-loat · nu-nhe-nhang · nu-nhan-nha · nu-calm · nu-cham
SAMPLE = "nu-calm.wav"  # đổi file -> đổi chất giọng
SPEED = 1.18  # >1 = đọc nhanh hơn
PITCH = 0.95  # >1 = trẻ/cao hơn; 1.0 = gốc; ~1.2 là ngưỡng trước khi méo
SR = 30000  # base sample-rate phát (kết hợp PITCH để chỉnh cao độ)
# ===================================================

ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = ROOT / "voices" / "viXTTS"
REF_WAV = MODEL_DIR / "samples" / SAMPLE

_model = None
_gpt_latent = None
_speaker_emb = None

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
    return re.sub(r"\s+", " ", text).strip()


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p for p in parts if p.strip()] or [text.strip()]


def _load():
    """Nạp viXTTS 1 lần (lazy)."""
    global _model, _gpt_latent, _speaker_emb
    if _model is not None:
        return
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts

    config = XttsConfig()
    config.load_json(str(MODEL_DIR / "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=str(MODEL_DIR), use_deepspeed=False)
    model.cuda()

    # Vá tokenizer để chấp nhận tiếng Việt ("vi")
    _orig = model.tokenizer.preprocess_text.__func__

    def _pre_vi(self, txt, lang):
        if lang == "vi":
            return re.sub(r"\s+", " ", txt.strip())
        return _orig(self, txt, lang)

    model.tokenizer.preprocess_text = types.MethodType(_pre_vi, model.tokenizer)

    _gpt_latent, _speaker_emb = model.get_conditioning_latents(audio_path=[str(REF_WAV)])
    _model = model


def preload() -> None:
    """Gọi sớm (lúc khởi động Luna) để câu nói đầu không bị khựng."""
    _load()


def speak(text: str) -> None:
    """Đọc câu tiếng Việt qua loa bằng giọng viXTTS (chặn tới khi đọc xong)."""
    text = _normalize(text)
    if not text:
        return
    _load()

    chunks = []
    for sent in _split_sentences(text):
        out = _model.inference(
            sent,
            "vi",
            _gpt_latent,
            _speaker_emb,
            temperature=0.7,
            speed=SPEED / PITCH,
            enable_text_splitting=False,
        )
        chunks.append(np.asarray(out["wav"], dtype=np.float32))

    if not chunks:
        return
    audio = np.clip(np.concatenate(chunks), -1, 1)
    sd.play(audio, int(SR * PITCH))  # phát ở SR cao hơn -> nâng cao độ
    sd.wait()


if __name__ == "__main__":
    # Nghe thử nhanh + chỉnh SAMPLE/SPEED/PITCH:
    #   python -m luna.voice.tts_vixtts "Câu muốn nghe"
    import sys

    demo = " ".join(sys.argv[1:]) or "Dạ, em là Luna. Anh nghe giọng em thế này ổn chưa ạ?"
    print(f"SAMPLE={SAMPLE}  SPEED={SPEED}  PITCH={PITCH}  SR={SR}")
    print("Đang nạp viXTTS...")
    speak(demo)
