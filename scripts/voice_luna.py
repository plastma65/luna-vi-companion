"""Luna nói chuyện hai chiều bằng giọng: mic -> STT -> Luna -> TTS -> loa.

Chạy trong .venv (TTS viXTTS chạy ngay trong tiến trình này, không cần server):
    python scripts/voice_luna.py
Hoặc bấm đúp Luna_Voice.bat / Luna_Jarvis.bat (có orb).

Cách dùng: cứ nói tự nhiên, im lặng ~3 giây là Luna hiểu anh nói xong.
Nói "tạm biệt" (hoặc Ctrl+C) để thoát.
"""

import re  # tách câu khi streaming
import sys
import threading
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel
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
from luna.voice.tts_vixtts import speak, preload  # viXTTS trong tiến trình (không server)
from luna.rag.retrieve import make_prompt, sources_line
from luna.farewell import is_farewell, GOODBYE_TEXT, GOODBYE_DISPLAY

# Khi chạy bằng pythonw (không console): stdout=None -> ghi log ra file, tránh print lỗi
if sys.stdout is None or sys.stderr is None:
    _ld = Path(__file__).resolve().parents[1] / "logs"
    _ld.mkdir(exist_ok=True)
    _lf = open(_ld / "voice.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _lf
    sys.stderr = sys.stderr or _lf

SR = 16000
SYSTEM = (
    "Bạn là Luna, một người bạn đồng hành AI người Việt. Luna xưng 'em' và gọi "
    "người dùng là 'anh'. Tính cách điềm đạm, ấm áp, chu đáo. Trả lời ngắn gọn, "
    "tự nhiên bằng tiếng Việt, thỉnh thoảng dùng emoji vừa phải. "
    "Nếu không chắc chắn hoặc không biết, em thành thật nói chưa rõ chứ không bịa."
)

# Gợi ý câu lệnh + thuật ngữ để STT nghe đúng hơn các từ tiếng Anh/công nghệ
STT_PROMPT = (
    "Câu lệnh cho trợ lý Luna: mở Discord, mở Google, mở YouTube, "
    "tìm trên Google, tìm trên YouTube, bây giờ mấy giờ, hôm nay ngày mấy. "
    "Chủ đề công nghệ: nmap, SQL injection, Python, pentest, Discord, Google, YouTube."
)

# Các câu Whisper hay 'ảo giác' khi im lặng — cần lọc bỏ
HALLUCINATIONS = [
    "ghiền mì gõ",
    "subscribe",
    "đăng ký kênh",
    "hẹn gặp lại trong video",
    "cảm ơn các bạn đã theo dõi",
    "cảm ơn các bạn đã lắng nghe",
    "cảm ơn các bạn đã xem",
    "like và đăng ký",
    "hẹn gặp lại trong video tiếp theo",
]

# ---------- 1) Nạp STT ----------
print("Đang nạp STT (faster-whisper)...")
stt = WhisperModel("small", device="cuda", compute_type="float16")

# ---------- 2) Nạp Luna (Qwen + adapter) ----------
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
print("✅ Sẵn sàng! (giọng viXTTS chạy trong tiến trình, không cần server)")


def measure_ambient(seconds: float = 1.2) -> float:
    """Đo mức tiếng ồn nền (RMS trung vị) để đặt ngưỡng nghe phù hợp mic."""
    block = int(SR * 0.1)
    vals = []
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=block) as stream:
        for _ in range(int(seconds / 0.1)):
            data, _ = stream.read(block)
            vals.append(float(np.sqrt(np.mean(data.flatten() ** 2))))
    vals.sort()
    return vals[len(vals) // 2]


def listen_for_utterance(threshold: float, silence_dur=3.0, max_utt=30) -> np.ndarray:
    """Rảnh tay: tự chờ tới khi anh cất tiếng, thu tới khi im ~silence_dur giây thì dừng.

    Có thanh mức âm để anh thấy mic có nghe mình không, và đệm đầu câu (pre-roll).
    """
    block = int(SR * 0.1)  # 100ms mỗi khối
    frames: list[np.ndarray] = []
    pre = deque(maxlen=10)  # giữ ~1 giây trước khi bắt đầu nói (chống cụt đầu câu)
    started, silence_t, spoke_t = False, 0.0, 0.0

    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=block) as stream:
        while True:
            data, _ = stream.read(block)
            data = data.flatten()
            rms = float(np.sqrt(np.mean(data**2)))

            if not started:
                bars = min(int(rms / max(threshold, 1e-6) * 8), 24)
                print("\r🎧 nghe |" + "█" * bars + " " * (24 - bars) + "|", end="", flush=True)
                pre.append(data)
                if rms > threshold:  # anh bắt đầu nói
                    started = True
                    frames.extend(pre)  # gắn cả phần đệm đầu câu
                    print("  ● đang thu...", end="", flush=True)
                continue

            frames.append(data)
            spoke_t += 0.1
            if rms > threshold:
                silence_t = 0.0
            else:
                silence_t += 0.1
                if silence_t >= silence_dur:  # im đủ lâu -> coi như nói xong
                    break
            if spoke_t > max_utt:
                break

    print()  # xuống dòng sau thanh mức âm
    if not frames:
        return np.zeros(1, dtype=np.float32)
    audio = np.concatenate(frames)
    trim = int((silence_dur - 0.3) * SR)  # cắt bớt im lặng đuôi
    if len(audio) > trim + int(0.3 * SR):
        audio = audio[:-trim]
    return audio


def transcribe_audio(audio: np.ndarray) -> str:
    """Chuyển audio -> chữ, có chống ảo giác của Whisper."""
    if len(audio) < SR * 0.3:  # quá ngắn (chưa tới 0.3s) -> bỏ
        return ""
    segments, _ = stt.transcribe(
        audio,
        language="vi",
        beam_size=5,
        vad_filter=True,  # lọc đoạn không phải tiếng nói
        condition_on_previous_text=False,  # tránh 'trôi' theo câu trước
        no_speech_threshold=0.5,
        initial_prompt=STT_PROMPT,
    )
    parts = []
    for s in segments:
        if getattr(s, "no_speech_prob", 0.0) > 0.6:
            continue
        parts.append(s.text.strip())
    text = " ".join(parts).strip()
    low = text.lower()
    if any(bad in low for bad in HALLUCINATIONS):
        return ""
    return text


def luna_reply_stream(history: list[dict]):
    """Sinh câu trả lời theo LUỒNG: vừa nghĩ vừa nhả ra từng CÂU hoàn chỉnh.

    Nhờ vậy Luna nói câu đầu ngay trong khi đang nghĩ câu tiếp theo (streaming).
    """
    prompt = tok.apply_chat_template(history, tokenize=False, add_generation_prompt=True)
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

    buf = ""
    for piece in streamer:
        buf += piece
        while True:
            m = re.search(r"[.!?…\n]", buf)  # gặp dấu kết câu -> nhả câu đó ra
            if not m:
                break
            i = m.end()
            sent = buf[:i].strip()
            buf = buf[i:]
            if sent:
                yield sent
    if buf.strip():
        yield buf.strip()


# (Câu thoát nay dùng chung ở luna/farewell.py — xem is_farewell)
# (Đã bỏ wait_for_tts: TTS chạy trong tiến trình, không còn server cổng 5111)


def main() -> None:
    history = [{"role": "system", "content": SYSTEM + facts_block()}]  # nạp trí nhớ
    print("\nĐang đo tiếng ồn nền (anh im lặng ~1 giây)...")
    ambient = measure_ambient()
    threshold = max(ambient * 4.0, 0.010)  # cao hơn -> ít bắt tiếng ồn/ảo giác
    print(f"Ngưỡng nghe: {threshold:.4f} (ồn nền {ambient:.4f})")
    print("\n=== Luna đang lắng nghe (chế độ rảnh tay, kiểu Jarvis) ===")
    print("Anh nói tự nhiên; thanh 🎧 sẽ nhảy theo giọng anh. Im ~3 giây là em trả lời.")
    print("Nói 'tạm biệt' hoặc nhấn Ctrl+C để thoát.\n")
    while True:
        orb("idle", "🎧 Đang lắng nghe...")
        audio = listen_for_utterance(threshold)

        user_text = transcribe_audio(audio)
        if not user_text:
            continue  # chỉ là tiếng ồn, nghe tiếp
        print("Anh:", user_text)
        log_turn("user", user_text)
        orb("thinking", "Đang suy nghĩ...")

        if is_farewell(user_text):  # chỉ cần nói "tạm biệt", không cần kèm tên
            print("Luna:", GOODBYE_DISPLAY)
            orb("speaking", GOODBYE_TEXT)
            speak(GOODBYE_TEXT)  # speak() chặn -> nói xong mới thoát
            orb("idle", "")
            break

        # Lệnh bộ nhớ (nhớ/quên/em nhớ gì) -> xử lý và cập nhật trí nhớ vào system prompt
        mem_reply = mem_cmd(user_text)
        if mem_reply is not None:
            history[0]["content"] = SYSTEM + facts_block()
            print("Luna:", mem_reply)
            log_turn("assistant", mem_reply)
            orb("speaking", mem_reply)
            speak(mem_reply)
            continue

        # Thử skill (ngày giờ, mở app, tìm kiếm). Nếu là lệnh -> chạy luôn.
        skill_reply = skill_route(user_text)
        if skill_reply:
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": skill_reply})
            print("Luna:", skill_reply)
            orb("speaking", skill_reply)
            speak(skill_reply)
            continue

        # RAG: tra tài liệu liên quan (không có gì đạt ngưỡng -> trò chuyện thường)
        asked, hits = make_prompt(user_text)
        if hits:
            print(f"   🔎 (tra cứu {len(hits)} đoạn tài liệu)")

        history.append({"role": "user", "content": asked})
        parts = []
        for sent in luna_reply_stream(history):  # vừa nghĩ vừa nói từng câu
            print("Luna:", sent)
            orb("speaking", sent)
            speak(sent)
            parts.append(sent)
        history[-1]["content"] = user_text  # chỉ giữ câu gốc trong lịch sử
        if hits:
            print("  ", sources_line(hits))  # in nguồn, không đọc thành tiếng
        full = " ".join(parts).strip()
        history.append({"role": "assistant", "content": full})
        log_turn("assistant", full)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nLuna:", GOODBYE_DISPLAY)
        try:
            speak(GOODBYE_TEXT)  # Ctrl+C cũng được chào tử tế
        except Exception:  # noqa: BLE001
            pass
