# ROADMAP — Lộ trình xây dựng Luna

Đọc file này trước tiên. Nó trả lời câu hỏi lớn của bạn: **"Làm được không?"** và **"Đi theo thứ tự nào?"**.

---

## Trả lời thẳng: Có làm được không?

**Có — nhưng cần hiểu đúng kỳ vọng.**

Tách rõ 2 việc mà nhiều người hay gộp làm một:

1. **Xây "bộ não" (model ngôn ngữ) từ đầu, chất lượng như Neuro-sama.**
   Neuro-sama đứng trên một LLM cỡ nhiều tỷ tham số, được train trên hàng nghìn tỷ chữ với hàng triệu đô GPU. **Một người tự train từ số 0 để đạt mức đó là không khả thi** — không phải vì bạn thiếu giỏi, mà vì thiếu dữ liệu + GPU ở quy mô đó. Hãy gạch bỏ kỳ vọng "tự viết GPT từ 0 rồi nó nói chuyện mượt như Neuro".

2. **Có một "Luna" thật sự chạy được, tính cách riêng, tiếng Việt, offline, weights của bạn.**
   **Việc này hoàn toàn khả thi trên RTX 3060 của bạn** bằng cách: *fine-tune* (huấn luyện lại phần ngọn) một model open-weights có sẵn. Weights sau fine-tune là của bạn, chạy offline, không gọi API ai cả. Đây chính là cách các "AI VTuber" chỉ-một-người thực sự làm.

Vì bạn chọn hướng **Hybrid**, ta tận dụng cả hai:
- **1a**: tự viết + train một *mini-GPT* từ số 0 → để **hiểu bản chất** Transformer hoạt động thế nào (kết quả sẽ "ngô nghê", đó là bình thường và đúng mục đích học).
- **1b**: fine-tune một model open-weights thành **Luna dùng thật**.

> Nguyên tắc "không phụ thuộc API/Ollama" vẫn được giữ: model open-weights (vd Qwen) là **file trọng số mở**, bạn tải về train lại và tự chạy bằng code của mình — khác hoàn toàn với gọi API Claude/Google hay để Ollama làm bộ não.

---

## Bản đồ giai đoạn

| GĐ | Tên | Kết quả | Độ khó | Ước lượng |
|----|-----|---------|--------|-----------|
| 0  | Nền tảng | Môi trường chạy, Python cơ bản, GPU nhận | ★☆☆☆☆ | 1–2 tuần |
| 1a | Mini-GPT từ 0 | Tự train GPT ~10M tham số sinh chữ tiếng Việt (ngô nghê) | ★★★☆☆ | 2–4 tuần |
| 1b | Luna thật (fine-tune) | Chatbot tính cách Luna, tiếng Việt, chạy offline | ★★★☆☆ | 3–6 tuần |
| 2  | Skills | Luna tra Google/YouTube, nói chuyện qua Discord | ★★★☆☆ | 4–8 tuần |
| 3  | Tự học | Ghi nhớ hội thoại, fine-tune định kỳ từ log | ★★★★☆ | dài hạn |
| 4  | UI Jarvis | App chạy nền Windows, giọng nói, overlay | ★★★★☆ | song song từ GĐ2 |

Thời gian là ước lượng cho người mới, học bán thời gian. Không phải deadline.

---

## GĐ 0 — Nền tảng (làm trước, đừng bỏ qua)

Mục tiêu: chạy được Python, hiểu tensor, GPU nhận card.

- [ ] Cài Python 3.11, tạo `.venv`, cài `requirements.txt` (xem README).
- [ ] `torch.cuda.is_available()` trả `True`.
- [ ] Ôn Python đủ dùng: biến, hàm, list/dict, class, đọc/ghi file. (Không cần giỏi, cần đủ.)
- [ ] Hiểu 3 khái niệm: **tensor**, **gradient**, **training loop** (xem `docs/GLOSSARY.md`).

Kiểm chứng: chạy được `pytest -q` (test smoke có sẵn trong `tests/`).

## GĐ 1a — Mini-GPT từ số 0 → **BẮT ĐẦU Ở ĐÂY**

Mục tiêu: **hiểu**, không phải để đẹp. Tự tay viết tokenizer, mô hình Transformer nhỏ, vòng lặp train; train trên một corpus tiếng Việt nhỏ (vd truyện, phụ đề) để nó học sinh chữ.

- [ ] Chuẩn bị corpus text tiếng Việt (~vài MB là đủ để học).
- [ ] Viết **tokenizer mức ký tự** (đơn giản nhất).
- [ ] Viết mô hình GPT nhỏ (~10M tham số): embedding, self-attention, block, head.
- [ ] Viết training loop, train vài nghìn step trên RTX 3060.
- [ ] Sinh thử văn bản — chấp nhận kết quả "lảm nhảm có vần". Đó là thành công của GĐ này.

👉 Hướng dẫn code từng dòng: **`guides/phase1a_mini_gpt.md`**.
Kiểm chứng: `tests/test_mini_gpt.py` xanh + sinh được text không lỗi.

## GĐ 1b — Luna thật bằng fine-tune (QLoRA)

Mục tiêu: có Luna nói tiếng Việt, có tính cách, chạy offline trên 3060.

- [ ] Chọn base model open-weights mạnh tiếng Việt (đề xuất **Qwen2.5-3B-Instruct**, vừa 12GB; có thể thử 7B với 4-bit).
- [ ] Viết **dataset tính cách Luna**: 300–1000 cặp (câu người dùng → câu Luna trả lời) theo giọng bạn muốn.
- [ ] Fine-tune bằng **QLoRA** (LoRA 4-bit) — chỉ train vài triệu tham số adapter, vừa VRAM.
- [ ] Gộp adapter, chạy inference offline bằng code của mình.

👉 Hướng dẫn: **`guides/phase1b_finetune.md`** (viết ở bước sau, khi bạn xong 1a).
Kiểm chứng: Luna trả lời đúng persona trên 10 câu test cố định (`tests/test_persona.py`).

## GĐ 2 — Skills (kết nối thế giới)

Luna gọi được công cụ ngoài. Kiến trúc: model quyết định *gọi skill nào*, code Python *thực thi* rồi đưa kết quả lại cho model.

- [ ] Khung "tool-calling" đơn giản (model xuất JSON `{skill, args}` → dispatcher chạy).
- [ ] Skill `web_search` (Google/DuckDuckGo), `youtube` (tìm/tra cứu), `discord` (chat 2 chiều).
- [ ] Mỗi skill là 1 file trong `src/luna/skills/`, có test riêng.

Ranh giới an toàn: skill thao tác máy tính phải **hỏi xác nhận** (xem `CLAUDE.md` §6).

## GĐ 3 — Tự học (sau khi Luna "sống")

Không có phép màu "AI tự nâng cấp". "Tự học" thực tế = vòng lặp dữ liệu:
- [ ] Ghi log hội thoại + phản hồi (bạn 👍/👎).
- [ ] Bộ nhớ dài hạn: lưu sự kiện quan trọng (vector DB nhỏ) để nhớ giữa các phiên.
- [ ] Định kỳ **fine-tune lại** adapter từ log đã được lọc → Luna "tiến bộ".
- [ ] Có bộ chặn để tránh học phải nội dung xấu / lệch persona.

## GĐ 4 — UI Jarvis chạy nền Windows

- [ ] Tiến trình nền (system tray) + hotkey gọi Luna.
- [ ] Overlay/hộp chat; sau đó thêm **giọng nói**: STT (nghe) + TTS (nói) tiếng Việt.
- [ ] Kiến trúc: backend Python (model + skills) ↔ UI (Electron/Tauri hoặc PyQt). Tách 2 lớp để dễ thay.

---

## GĐ 5 — Di sản: đưa Luna lên GitHub (làm ở cuối, nhưng git init nên làm sớm)

Mục tiêu: Luna sống tiếp và người khác nối tiếp được, kể cả khi chủ dự án không còn tham gia.

- [ ] `git init`, đưa dự án lên một repo GitHub (nên làm SỚM để có lịch sử phiên bản).
- [ ] Thêm **LICENSE** mở (MIT hoặc Apache-2.0) + README rõ ràng + file `CONTINUE_LUNA.md` hướng dẫn người sau tiếp tục.
- [ ] Script `scripts/push_luna.ps1`: tự `git add/commit/push` bản mới nhất.
- [ ] Đăng ký chạy tự động định kỳ bằng **Windows Task Scheduler** → repo luôn được sao lưu công khai.
- [ ] KHÔNG commit weights/dataset lớn/secret (đã có `.gitignore`).

Thiết kế "luôn sao lưu công khai" đáng tin hơn kiểu "kích hoạt khi vắng mặt". Nếu muốn thêm cơ chế kích hoạt theo thời gian không hoạt động (dead-man switch), làm sau, dựa trên nền này.

## Thứ tự khuyến nghị làm ngay
1. GĐ 0 (môi trường) → 2. GĐ 1a (mini-GPT) → 3. GĐ 1b (Luna thật).
Chỉ khi có Luna trả lời được mới sang skills/UI. **Đừng làm UI trước khi có bộ não.**
