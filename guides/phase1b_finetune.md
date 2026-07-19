# Guide 1b — Fine-tune Luna thật bằng QLoRA

> Mục tiêu: Luna **nói tiếng Việt có nghĩa, đúng tính cách**, chạy **offline** trên RTX 3060 — bằng cách fine-tune một model open-weights, KHÔNG gọi API ai cả.
>
> Khác Giai đoạn 1a: 1a bạn tự viết model từ 0 để *hiểu*. 1b ta đứng trên vai người khổng lồ — lấy một model đã học tiếng Việt sẵn rồi *dạy thêm tính cách Luna*. Đây mới là "Luna dùng thật".

## Vì sao không train từ 0 nữa?

Model như Qwen3 được train trên hàng nghìn tỷ chữ bằng cụm GPU triệu đô — thứ ta không thể tái tạo. Nhưng weights của nó **mở**: tải về, train thêm một lớp mỏng (adapter) trên dữ liệu của bạn là đủ đổi "giọng" và "tính cách". Đó là **fine-tune**. Weights sau khi train là của bạn, chạy offline. Vẫn đúng nguyên tắc dự án.

## Khái niệm cốt lõi (đọc `docs/GLOSSARY.md` nếu cần)

- **LoRA**: thay vì train lại toàn bộ vài tỷ tham số, ta "đóng băng" model gốc và chỉ chèn thêm vài triệu tham số nhỏ (adapter). Rẻ, nhanh, vừa VRAM.
- **QLoRA**: LoRA + nén model gốc xuống **4-bit** để đỡ tốn VRAM. Nhờ đó Qwen3-4B vừa gọn trong 12GB.
- **SFT (Supervised Fine-Tuning)**: dạy model bằng các cặp *(câu người dùng → câu trả lời mẫu)*.
- **Chat template**: mỗi model có định dạng riêng để đánh dấu "đây là lời người dùng / đây là lời trợ lý". Ta phải theo đúng template của Qwen.

## Model nền

**Chính:** `Qwen/Qwen3-4B-Instruct-2507` — tiếng Việt tốt, ~3GB ở 4-bit, QLoRA thoải mái trên RTX 3060.
**Dự phòng (nhẹ hơn):** `Qwen/Qwen2.5-3B-Instruct`.

Model tải tự động từ Hugging Face lần chạy đầu (~vài GB, cần mạng). Qwen giấy phép Apache-2.0, không cần token.

---

## Bước 1 — Cài thư viện

Bỏ comment các dòng 1b trong `requirements.txt` rồi cài, hoặc cài trực tiếp:

```powershell
pip install "transformers>=4.44" "datasets>=2.20" "peft>=0.12" "accelerate>=0.33" "trl>=0.9" bitsandbytes
```

Kiểm tra bitsandbytes nhận CUDA:
```powershell
python -c "import bitsandbytes as bnb; print('bitsandbytes OK')"
```
In `bitsandbytes OK` là ổn. (Nếu lỗi DLL/CUDA, báo mình — có cách xử lý riêng trên Windows.)

## Bước 2 — Dựng dataset tính cách Luna

Đây là phần **quyết định tính cách**. Format: mỗi dòng 1 JSON gồm `messages` theo chuẩn chat.

File `data/processed/luna_persona.jsonl`, mỗi dòng như:
```json
{"messages": [{"role": "system", "content": "Bạn là Luna, trợ lý ảo tiếng Việt, tính cách hoạt bát, tinh nghịch, nói ngắn gọn tự nhiên."}, {"role": "user", "content": "Chào Luna"}, {"role": "assistant", "content": "Hí, chào cậu chủ! Luna sẵn sàng quậy rồi đây, cần gì nào?"}]}
```

Nguyên tắc data:
- **Chất > lượng**: 300–1000 mẫu tốt hơn 5000 mẫu cẩu thả. Khởi đầu ~40 mẫu để chạy thử pipeline, rồi mở rộng.
- **Nhất quán giọng**: cùng một Luna trong mọi câu, tránh "đa nhân cách".
- **Đa dạng tình huống**: chào hỏi, hỏi đáp kiến thức, từ chối lịch sự, pha trò, an ủi, hướng dẫn.
- **System prompt cố định** mô tả Luna, lặp lại ở mọi mẫu.

Script kiểm tra dataset hợp lệ: `scripts/check_dataset.py` (viết ở bước thực hành).

## Bước 3 — Smoke test pipeline

Trước khi train thật (tốn thời gian + tải model), chạy 2 step trên 2–3 mẫu để chắc không vỡ. Xem `tests/test_finetune_smoke.py` (đánh dấu `slow`, cần mạng/GPU nên tách khỏi test thường).

## Bước 4 — Train QLoRA

Script `scripts/train_luna_sft.py`:
- Nạp Qwen3-4B ở 4-bit (`BitsAndBytesConfig`).
- Gắn LoRA (`LoraConfig`, target các lớp attention).
- Dùng `SFTTrainer` (thư viện `trl`) train trên `luna_persona.jsonl`.
- Lưu **adapter** vào `checkpoints/luna_lora/` (chỉ vài chục MB, không phải cả model).

Siêu tham số khởi đầu (an toàn cho 12GB): `r=16, lora_alpha=32, batch_size=1, grad_accum=8, lr=2e-4, epochs=3, max_seq_len=1024`.

## Bước 5 — Chat với Luna (offline)

Script `scripts/chat_luna_sft.py`: nạp base 4-bit + adapter, áp chat template, trò chuyện trong terminal. Đây là lần đầu Luna trả lời **có nghĩa + đúng giọng**.

## Bước 6 — Persona test

`tests/test_persona.py`: 10 câu cố định, kiểm câu trả lời giữ đặc trưng Luna (vd xưng "Luna"/"tớ", giọng vui). Không đo "thông minh", chỉ đo *nhất quán tính cách*.

---

## Lỗi thường gặp (điền dần khi ta gặp)
- **CUDA out of memory**: giảm `max_seq_len`, `batch_size=1`, tăng `grad_accum`, hoặc đổi sang Qwen2.5-3B.
- **bitsandbytes lỗi DLL trên Windows**: cập nhật bản mới nhất; kiểm CUDA của PyTorch khớp.
- **Adapter không đổi giọng**: data quá ít/không nhất quán, hoặc lr quá nhỏ — tăng dữ liệu, train thêm epoch.

Ta sẽ đi từng bước trong chat, mỗi bước chạy được mới sang tiếp — y như Giai đoạn 1a.
