# TRẠNG THÁI DỰ ÁN LUNA

Cập nhật: các mốc đã hoàn thành, cách chạy, và việc sắp tới.

## ✅ Đã làm được

**Giai đoạn 0 — Nền tảng**
- Môi trường Python 3.11 + venv, PyTorch CUDA, GPU RTX 3060 nhận.

**Giai đoạn 1a — Mini-GPT từ số 0**
- Tự viết tokenizer (`src/luna/core/tokenizer.py`) + model GPT (`model.py`).
- Train trên corpus tiếng Việt 0.6MB → sinh được tiếng Việt (bản học tập).
- Chạy: `scripts/train_luna.py`, `scripts/chat_luna.py`. Test: `pytest -q`.

**Giai đoạn 1b — Luna thật (QLoRA)**
- Fine-tune `Qwen3-4B-Instruct-2507` bằng QLoRA trên 45 mẫu tính cách.
- Persona: xưng "em" gọi "anh", điềm đạm ấm áp, dùng emoji vừa phải.
- Adapter lưu ở `checkpoints/luna_lora/`.

**Giai đoạn 4 — Giọng nói + Giao diện Jarvis**
- STT: `faster-whisper` (nghe tiếng Việt), có chống ảo giác + gợi ý thuật ngữ.
- TTS: `viXTTS` (giọng nữ tiếng Việt) chạy **trong tiến trình** — KHÔNG cần server riêng nữa.
  Module: `src/luna/voice/tts_vixtts.py`; chỉnh `SAMPLE`/`SPEED`/`PITCH` để đổi giọng;
  nghe thử: `python -m luna.voice.tts_vixtts "câu thử"`. (Cần `coqui-tts` + `transformers>=4.57,<5` trong `.venv`.)
- Vòng thoại rảnh tay kiểu Jarvis (`voice_luna.py`): tự nghe → nghĩ → nói.
- Orb overlay (`overlay.py`): quả cầu trong suốt, luôn nổi, đổi hiệu ứng idle/thinking/speaking + pill chữ.
- Khởi động chỉ 2 tiến trình (orb + Luna), chạy ẩn bằng `Luna.vbs`, dừng bằng `Luna_Stop.vbs`.
  `.venv-tts` và `scripts/tts_server.py` đã **ngưng dùng** (có thể xoá `.venv-tts` cho nhẹ).

**Giai đoạn 2 — Skills (khởi đầu)**
- `src/luna/skills/commands.py`: xem ngày giờ, mở Google/YouTube/Discord, tìm Google/YouTube.
- Router hiểu cả cách STT nghe nhầm ("gu gồ", "diu túp"...).

## ▶️ Cách chạy (4 chế độ)

| File bấm đúp | Anh nhập | Luna trả lời | Orb |
|---|---|---|---|
| `Luna.bat` | gõ chữ | chữ | — |
| `Luna_ChatVoice.bat` | gõ chữ | giọng | (mở riêng) |
| `Luna_Voice.bat` | nói | giọng | — |
| `Luna_Jarvis.bat` ⭐ | nói | giọng | có |

## ⚠️ Giới hạn hiện tại
- Luna **fine-tune giỏi tính cách, không chắc kiến thức** → hỏi kiến thức lạ có thể bịa. Sẽ khắc phục bằng RAG.
- STT thỉnh thoảng nghe nhầm từ tiếng Anh; câu ngắn hoặc phòng ồn có thể lệch.
- Cần GPU đủ mạnh (RTX 3060) cho trải nghiệm mượt.

## ⏭️ Sắp tới
1. ~~Streaming TTS~~ ✅ — Luna đọc từng câu ngay khi nghĩ xong.
2. ~~RAG cho Luna~~ ✅ — trả lời an ninh mạng dựa trên OWASP/nmap/Metasploit, có trích nguồn, chống bịa bằng ngưỡng điểm.
3. ~~Giai đoạn 5 — Di sản~~ ✅ — code trên GitHub (`Luna_Backup.bat` để sao lưu). Ký ức riêng (`facts.json`) ở lại máy.
4. **Bộ cài .exe** — `install.bat` + `installer/luna_setup.iss` (Inno Setup) → `Luna_Setup.exe`. Xem `guides/installer_exe.md`. ← đang hoàn thiện
5. **Nhánh "Luna Lite"** — cấu hình nhẹ cho máy yếu (laptop 8GB): model nhỏ + giọng piper, hoặc laptop làm client nối tới Luna trên máy khoẻ.
