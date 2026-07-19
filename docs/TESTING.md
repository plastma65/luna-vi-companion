# TESTING.md — Quy tắc kiểm thử dự án Luna

Người mới hay bỏ test. Trong dự án này **test là bắt buộc** — nó là tấm lưới an toàn giúp bạn sửa/mở rộng mà không sợ làm hỏng phần cũ.

## 1. Nguyên tắc vàng
1. **Không có tính năng nào "xong" nếu chưa có test và `pytest` chưa xanh.**
2. **Mỗi khi thêm code, thêm ít nhất 1 test.** Sửa bug → thêm test tái hiện bug đó trước khi sửa.
3. **Test phải chạy nhanh và offline** — không gọi mạng thật, không cần GPU. Mock những thứ ngoài.
4. **Với code training: luôn có "smoke test"** — chạy 1–2 step trên dữ liệu tí hon để chắc pipeline không vỡ, TRƯỚC khi train thật hàng giờ.

## 2. Lệnh kiểm tra chuẩn (chạy trước khi báo "xong")
```powershell
ruff check .          # lint: bắt lỗi cú pháp/style
black --check .        # format đúng chuẩn chưa
pytest -q              # chạy toàn bộ test
```
Cả 3 xanh mới được coi là hoàn thành một bước.

## 3. Cấu trúc test
- Thư mục `tests/`, file đặt tên `test_*.py`, hàm `test_*`.
- Mỗi module `src/luna/xxx.py` nên có `tests/test_xxx.py` tương ứng.
- Dùng `pytest` + `assert` thường (không cần framework phức tạp).

## 4. Các loại test trong dự án

### a) Smoke test (quan trọng nhất cho ML)
Chạy pipeline ở quy mô tí hon để chắc "không vỡ". Ví dụ mini-GPT:
- tạo model bé xíu (vài chục nghìn tham số),
- train đúng 2 step trên 100 ký tự,
- kiểm tra loss là số hữu hạn (không NaN) và sinh được text.

Test này chạy trong vài giây, tách biệt hoàn toàn với "train thật".

### b) Unit test
Kiểm một hàm nhỏ cho kết quả đúng. Ví dụ: tokenizer `encode` rồi `decode` phải ra lại chuỗi gốc (round-trip).

### c) Persona test (GĐ1b)
10 câu hỏi cố định → kiểm câu trả lời của Luna có giữ đúng giọng/persona (kiểm bằng từ khoá hoặc chấm điểm đơn giản), không phải để đo "thông minh".

### d) Skill test (GĐ2)
Mock mạng (dùng `monkeypatch`/`unittest.mock`), kiểm skill trả `SkillResult` đúng khi thành công VÀ khi lỗi. KHÔNG gọi API thật trong test.

## 5. Quy ước loss/độ ổn định (ML)
- Loss phải là số hữu hạn; nếu ra `NaN`/`inf` → coi là **fail**, dừng train, hạ learning rate.
- Smoke test phải thấy loss **giảm** sau vài chục step trên dữ liệu nhỏ (bằng chứng học được).

## 6. Khi CI chưa có
Chưa cần CI online. Chỉ cần **tự chạy 3 lệnh ở §2 trước mỗi lần commit**. Có thể thêm Git hook sau.

## 7. Test mẫu có sẵn
Xem `tests/test_smoke.py` (đã tạo) — mẫu tối giản để bạn quen cấu trúc. Chạy thử ngay:
```powershell
pytest -q
```
