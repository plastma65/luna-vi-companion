"""Gõ chữ để hỏi, Luna trả lời bằng GIỌNG NÓI (input chữ -> output giọng).

Hữu ích để tách lỗi: bỏ mic ra, chỉ kiểm phần Luna suy nghĩ + phần giọng nói.

TTS chạy TRONG tiến trình (piper) -> KHÔNG cần server. Chỉ cần .venv:
    python scripts/chat_voice_luna.py
(Hoặc bấm đúp Luna_ChatVoice.bat.)
"""

import re
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextIteratorStreamer,
)
from peft import PeftModel

from luna.config import SFT, ADAPTER_DIR
from luna.skills.commands import route as skill_route
from luna.ui.overlay_client import set_state as orb
from luna.memory.store import memory_command as mem_cmd, facts_block, log_turn
from luna.rag.retrieve import make_prompt, sources_line
from luna.farewell import is_farewell, GOODBYE_TEXT, GOODBYE_DISPLAY
from luna.voice.tts_vixtts import speak, preload  # viXTTS trong tiến trình (không server)

SYSTEM = (
    "Bạn là Luna, một người bạn đồng hành AI người Việt. Luna xưng 'em' và gọi "
    "người dùng là 'anh'. Tính cách điềm đạm, ấm áp, chu đáo. Trả lời ngắn gọn, "
    "tự nhiên bằng tiếng Việt, thỉnh thoảng dùng emoji vừa phải. "
    "Nếu không chắc chắn hoặc không biết, em thành thật nói chưa rõ chứ không bịa."
)

print("Đang nạp Luna (base 4-bit + adapter)...")
bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
tok = AutoTokenizer.from_pretrained(SFT.base_model)
base = AutoModelForCausalLM.from_pretrained(
    SFT.base_model, quantization_config=bnb, device_map="auto", torch_dtype=torch.bfloat16
)
luna = PeftModel.from_pretrained(base, str(ADAPTER_DIR))
luna.eval()
print("Đang nạp giọng viXTTS (20-40 giây lần đầu)...")
preload()
print("🌙 Luna sẵn sàng! Gõ để hỏi, Luna trả lời bằng giọng. Gõ 'tạm biệt' để dừng.\n")

history = [{"role": "system", "content": SYSTEM + facts_block()}]

while True:
    user = input("Anh: ").strip()
    if not user:
        continue
    if is_farewell(user, typed=True):
        print("Luna:", GOODBYE_DISPLAY)
        orb("speaking", GOODBYE_TEXT)
        speak(GOODBYE_TEXT)  # speak() chặn tới khi đọc xong mới thoát
        orb("idle", "")
        break
    log_turn("user", user)

    # Lệnh bộ nhớ trước (nhớ/quên/em nhớ gì)
    mem_reply = mem_cmd(user)
    if mem_reply is not None:
        history[0]["content"] = SYSTEM + facts_block()
        print("Luna:", mem_reply)
        orb("speaking", mem_reply)
        speak(mem_reply)
        orb("idle", "")
        continue

    # Skill (mở app, tìm kiếm, ngày giờ)
    sk = skill_route(user)
    if sk:
        print("Luna:", sk)
        history.append({"role": "user", "content": user})
        history.append({"role": "assistant", "content": sk})
        orb("speaking", sk)
        speak(sk)
        orb("idle", "")
        continue

    orb("thinking", "Đang suy nghĩ...")

    # RAG: chèn tài liệu liên quan (nếu có) vào lượt hỏi này
    asked, hits = make_prompt(user)
    if hits:
        print(f"   🔎 (tra cứu {len(hits)} đoạn tài liệu)")

    history.append({"role": "user", "content": asked})
    prompt = tok.apply_chat_template(history, tokenize=False, add_generation_prompt=True)
    history[-1]["content"] = user  # chỉ lưu câu gốc, tránh phình ngữ cảnh
    inputs = tok(prompt, return_tensors="pt").to(luna.device)
    streamer = TextIteratorStreamer(tok, skip_prompt=True, skip_special_tokens=True)
    kwargs = dict(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.1,
        streamer=streamer,
    )
    threading.Thread(target=luna.generate, kwargs=kwargs, daemon=True).start()

    parts, buf = [], ""
    for piece in streamer:
        buf += piece
        while True:
            m = re.search(r"[.!?…\n]", buf)
            if not m:
                break
            i = m.end()
            sent = buf[:i].strip()
            buf = buf[i:]
            if sent:
                print("Luna:", sent)
                orb("speaking", sent)
                speak(sent)
                parts.append(sent)
    if buf.strip():
        print("Luna:", buf.strip())
        orb("speaking", buf.strip())
        speak(buf.strip())
        parts.append(buf.strip())
    if hits:
        print("  ", sources_line(hits))  # in nguồn, KHÔNG đọc thành tiếng
    history.append({"role": "assistant", "content": " ".join(parts).strip()})
    orb("idle", "")
