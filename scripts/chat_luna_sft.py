"""Chat với Luna sau fine-tune (base 4-bit + adapter LoRA), chạy offline.

Chạy:
    python scripts/chat_luna_sft.py

Gõ 'thoát' để dừng.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

from luna.config import SFT, ADAPTER_DIR
from luna.skills.commands import route as skill_route
from luna.memory.store import memory_command as mem_cmd, facts_block
from luna.rag.retrieve import make_prompt, sources_line
from luna.farewell import is_farewell, GOODBYE_DISPLAY

SYSTEM = (
    "Bạn là Luna, một người bạn đồng hành AI người Việt. Luna xưng 'em' và gọi "
    "người dùng là 'anh'. Tính cách điềm đạm, ấm áp, chu đáo. Trả lời ngắn gọn, "
    "tự nhiên bằng tiếng Việt, thỉnh thoảng dùng emoji vừa phải."
)

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
model = PeftModel.from_pretrained(base, str(ADAPTER_DIR))  # gắn adapter Luna
model.eval()

print("🌙 Luna sẵn sàng! Gõ 'tạm biệt' (hoặc 'thoát') để dừng.")
history = [{"role": "system", "content": SYSTEM + facts_block()}]

while True:
    user = input("Anh: ").strip()
    if is_farewell(user, typed=True):
        print("Luna:", GOODBYE_DISPLAY)
        break
    mem_reply = mem_cmd(user)
    if mem_reply is not None:
        history[0]["content"] = SYSTEM + facts_block()
        print("Luna:", mem_reply)
        history.append({"role": "user", "content": user})
        history.append({"role": "assistant", "content": mem_reply})
        continue
    sk = skill_route(user)
    if sk:
        print("Luna:", sk)
        history.append({"role": "user", "content": user})
        history.append({"role": "assistant", "content": sk})
        continue
    # RAG: tìm tài liệu liên quan. Không có gì đạt ngưỡng -> giữ nguyên câu hỏi,
    # Luna trò chuyện bình thường (ngưỡng min_score chính là 'công tắc' RAG).
    asked, hits = make_prompt(user)
    if hits:
        print(f"   🔎 (tra cứu {len(hits)} đoạn tài liệu)")

    # Gửi cho model bản CÓ ngữ cảnh, nhưng chỉ lưu câu gốc vào history
    # để ngữ cảnh không tích tụ qua các lượt làm phình cửa sổ ngữ cảnh.
    history.append({"role": "user", "content": asked})
    prompt = tok.apply_chat_template(history, tokenize=False, add_generation_prompt=True)
    history[-1]["content"] = user
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
        )
    reply = tok.decode(out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True).strip()
    print("Luna:", reply)
    if hits:
        print("  ", sources_line(hits))  # in nguồn để anh kiểm chứng
    history.append({"role": "assistant", "content": reply})
