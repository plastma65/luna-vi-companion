# 🌙 Luna — Người bạn đồng hành AI tiếng Việt, chạy hoàn toàn offline

Luna là một trợ lý/người bạn đồng hành AI **nói tiếng Việt**, chạy **100% trên máy
của bạn**: không gọi API của OpenAI/Google/Anthropic, không cần Internet khi dùng.
Trọng số model là của bạn — tự fine-tune, tự lưu, tự kiểm soát.

- 🗣️ **Nói chuyện bằng giọng nói** — nghe mic, trả lời bằng giọng nữ tiếng Việt tự nhiên
- 🧠 **Nhớ dài hạn** — nhớ những điều bạn dặn, giữ qua các lần bật/tắt
- 📚 **RAG an ninh mạng** — trả lời dựa trên tài liệu thật (OWASP, nmap, Metasploit) kèm trích nguồn
- 🔮 **Giao diện orb kiểu Jarvis** — quả cầu trong suốt nổi trên màn hình, phản ứng khi nghĩ/nói
- 🛠️ **Kỹ năng** — xem giờ, mở Google/YouTube/Discord, tìm kiếm, đếm số

> Dự án cá nhân, viết theo hướng **học để hiểu**: có `guides/` hướng dẫn từng bước
> từ train mini-GPT từ số 0 đến fine-tune QLoRA và dựng RAG.

---

## 📋 Yêu cầu

| Thành phần | Tối thiểu | Khuyến nghị |
|---|---|---|
| GPU | NVIDIA 8GB VRAM | **RTX 3060 12GB** trở lên |
| RAM | 16GB | 32GB |
| Ổ đĩa trống | ~15GB | 25GB |
| Hệ điều hành | Windows 10/11 | Windows 11 |
| Python | 3.11 | 3.11 |

Cần **GPU NVIDIA có CUDA**. Chạy CPU về lý thuyết được nhưng chậm tới mức không dùng nổi.

---

## 🚀 Cài đặt

### ⚡ Cách nhanh (khuyên dùng)

Đã có Python 3.11 và GPU NVIDIA? Chỉ cần **bấm đúp `install.bat`** — nó tự tạo môi
trường, cài thư viện, tải model và train Luna (~15–40 phút, tải ~10GB). Xong bấm
`Luna.vbs` để chạy.

Muốn đóng thành **file cài đặt `Luna_Setup.exe`** kiểu app Windows (Next → Finish)?
Xem `guides/installer_exe.md`.

> Cách thủ công từng bước ở dưới dành cho ai muốn hiểu rõ hoặc gỡ lỗi.

### 1. Tải mã nguồn

```powershell
git clone https://github.com/<tài-khoản-của-bạn>/Luna_Project.git
cd Luna_Project
```

### 2. Tạo môi trường ảo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
```

> Nếu PowerShell chặn script: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### 3. Cài PyTorch bản CUDA (làm TRƯỚC, đúng lệnh này)

```powershell
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Kiểm tra GPU đã nhận:
```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```
Phải in `True` và tên GPU của bạn.

### 4. Cài phần còn lại

```powershell
pip install -r requirements.txt
pip check          # phải báo "No broken requirements found."
```

> ⚠️ **Đừng nâng `transformers` lên 5.x.** Bản 5.x bỏ hàm `isin_mps_friendly`
> khiến `coqui-tts` (giọng nói) crash. File requirements đã ghim `>=4.57,<5`.

### 5. Tải giọng nói viXTTS

```powershell
python scripts\download_vixtts.py
```
Tải về `voices/viXTTS/` (~1.9GB). Nghe thử:
```powershell
cd src
python -m luna.voice.tts_vixtts "Chào anh, em là Luna"
cd ..
```

### 6. Huấn luyện tính cách Luna (QLoRA)

Repo **không kèm trọng số** (quá nặng). Bạn tự train — chỉ mất khoảng 10–20 phút:

```powershell
python scripts\train_luna_sft.py
```
Kết quả lưu ở `checkpoints/luna_lora/`. Model nền `Qwen3-4B-Instruct-2507` sẽ tự
tải từ Hugging Face lần đầu (~8GB).

Muốn đổi tính cách? Sửa `data/processed/luna_persona.jsonl` rồi train lại.

### 7. (Tuỳ chọn) Dựng kho tri thức an ninh mạng cho RAG

```powershell
python scripts\fetch_knowledge.py    # tải OWASP + man page nmap + docs Metasploit
python scripts\build_index.py        # dựng chỉ mục FAISS (~3-5 phút)
python scripts\ask_rag.py "SQL injection là gì"    # thử tra cứu
```

Muốn thêm tài liệu riêng (sách PDF, ghi chú)? Bỏ vào `data/knowledge/books/`
rồi chạy lại `build_index.py`.

---

## ▶️ Cách chạy

| Bấm đúp | Bạn nhập | Luna trả lời | Orb | Ghi chú |
|---|---|---|---|---|
| `Luna.bat` | gõ chữ | chữ | — | nhẹ nhất, dễ debug |
| `Luna_ChatVoice.bat` | gõ chữ | **giọng nói** | ✅ | khi mic không ổn |
| `Luna_Voice.bat` | **nói** | giọng nói | — | rảnh tay, có cửa sổ log |
| `Luna_Jarvis.bat` | **nói** | giọng nói | ✅ | đầy đủ, có cửa sổ log |
| `Luna.vbs` ⭐ | **nói** | giọng nói | ✅ | **chạy ẩn, chỉ hiện orb** |

Dừng Luna đang chạy ẩn: bấm đúp **`Luna_Stop.vbs`**.

### Nói chuyện với Luna

- Nói tự nhiên, im lặng ~3 giây là Luna trả lời.
- Kết thúc: nói (hoặc gõ) **"tạm biệt"** — Luna sẽ chào rồi tắt.
- Ghi nhớ: *"nhớ giúp anh: ..."*, *"ghi nhớ ..."*, *"hãy nhớ ..."*
- Nhắc lại: *"em nhớ gì về anh?"* · Xoá: *"quên ..."* / *"quên hết"*
- Kỹ năng: *"mấy giờ rồi?"*, *"mở YouTube"*, *"tìm Google ..."*, *"đếm từ 1 đến 20"*

---

## ⚙️ Tinh chỉnh

**Giọng nói** — `src/luna/voice/tts_vixtts.py`:
```python
SAMPLE = "nu-calm.wav"   # đổi file trong voices/viXTTS/samples/ để đổi chất giọng
SPEED  = 1.18            # >1 đọc nhanh hơn
PITCH  = 0.95            # >1 giọng trẻ/cao hơn
```
Nghe thử nhanh: `python -m luna.voice.tts_vixtts "câu thử"` (chạy trong `src/`).

**Tính cách** — sửa biến `SYSTEM` trong `scripts/chat_luna_sft.py` (và các script khác),
hoặc train lại với dataset mới.

**RAG** — `src/luna/config.py`, lớp `LunaRAGConfig`:
```python
top_k = 4            # số đoạn tài liệu đưa cho Luna đọc
min_score = 0.84     # dưới ngưỡng này coi như "không liên quan" (chống bịa)
```

**Nghe mic** — `scripts/voice_luna.py`: `silence_dur` (giây im lặng để kết thúc câu),
ngưỡng ồn nền tự đo lúc khởi động.

---

## 📁 Cấu trúc

```
Luna_Project/
├── src/luna/
│   ├── config.py           # cấu hình tập trung
│   ├── farewell.py         # nhận biết lời tạm biệt (dùng chung 3 chế độ)
│   ├── core/               # mini-GPT tự viết (phần học tập)
│   ├── memory/             # bộ nhớ dài hạn
│   ├── rag/                # chunk · embed · FAISS · retrieve
│   ├── skills/             # kỹ năng (giờ, mở app, tìm kiếm, đếm)
│   ├── voice/              # TTS viXTTS trong tiến trình
│   └── ui/                 # client điều khiển orb
├── scripts/                # train, chat, voice, overlay, RAG, tiện ích
├── guides/                 # 📖 hướng dẫn từng bước để tự code lại
├── docs/                   # ROADMAP · RAG · GLOSSARY · TESTING · PROGRESS
├── data/                   # dữ liệu (phần lớn KHÔNG commit)
├── checkpoints/            # adapter sau train (KHÔNG commit)
└── voices/                 # model giọng nói (KHÔNG commit)
```

---

## 🔒 Quyền riêng tư

Luna được thiết kế để **dữ liệu không rời khỏi máy bạn**:

- Không gọi API AI bên ngoài. Chỉ có mạng khi bạn chủ động tải model/tài liệu.
- `data/memory/facts.json` (những điều Luna nhớ về bạn) và nhật ký hội thoại
  **đã được `.gitignore`** — sẽ không bị đẩy lên GitHub.
- Kỹ năng điều khiển máy tính mặc định chỉ **mở** ứng dụng/trang web, không xoá,
  không gửi gì ra ngoài.

Nếu bạn fork dự án, **kiểm tra `git status` trước khi commit** để chắc chắn
`data/memory/` không lọt vào.

---

## 🧯 Lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `No module named 'TTS'` | `pip install coqui-tts` |
| `cannot import name 'isin_mps_friendly'` | `transformers` đang là 5.x → `pip install "transformers>=4.57,<5"` |
| `No module named 'torchaudio'` | Cài kèm torch: `pip install torchaudio --index-url https://download.pytorch.org/whl/cu121` (đúng phiên bản torch) |
| `No module named 'faiss'` | `pip install faiss-cpu` |
| `torch.cuda.is_available()` ra `False` | Cài nhầm torch bản CPU → gỡ rồi cài lại bằng lệnh `--index-url .../cu121` |
| Luna hành xử như code cũ sau khi sửa file | Xoá cache: `Remove-Item -Recurse -Force src\luna\**\__pycache__` |
| Chưa có chỉ mục RAG | `python scripts\build_index.py` |
| Mic không nghe / nghe sai | `python scripts\test_mic.py`, `python scripts\test_stt.py` |
| Orb không hiện | Chạy `python scripts\overlay.py` xem lỗi; cần `PySide6` |

---

## 🙏 Ghi công

- [Qwen3-4B-Instruct](https://huggingface.co/Qwen) — model nền (Alibaba)
- [viXTTS](https://huggingface.co/capleaf/viXTTS) — giọng nói tiếng Việt
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — nhận dạng giọng nói
- [OWASP](https://owasp.org) — tài liệu bảo mật (CC BY-SA)
- [Nmap](https://nmap.org) · [Metasploit](https://github.com/rapid7/metasploit-framework) — tài liệu công cụ

Tài liệu trong `data/knowledge/` do người dùng tự tải về, **không kèm trong repo**,
và thuộc giấy phép của tác giả gốc.

---

## ⚖️ Ghi chú về nội dung an ninh mạng

Phần RAG phục vụ **học tập và phòng thủ**. Chỉ kiểm thử trên hệ thống bạn sở hữu
hoặc được cho phép bằng văn bản. Tác giả không chịu trách nhiệm cho việc sử dụng sai.
