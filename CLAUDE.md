# CLAUDE.md — Quy tắc dự án Luna

> File này để Claude Code / trợ lý AI đọc mỗi khi làm việc trong repo này.
> Mục tiêu: giữ dự án nhất quán, an toàn, và **dạy người dùng tự viết code** thay vì làm hộ toàn bộ.

## 1. Bối cảnh dự án

Luna là một **trợ lý ảo AI** chạy trên Windows, tính cách hoạt bát kiểu Neuro-sama, giao tiếp **tiếng Việt là chính**.

Ràng buộc cốt lõi của chủ dự án (Lozens):
- **Tự train model**, KHÔNG phụ thuộc API bên ngoài (Claude, Google/Gemini, OpenAI) và KHÔNG dùng runtime local kiểu Ollama làm "bộ não". Weights phải là của Luna.
- Đi theo hướng **Hybrid**: Giai đoạn 1a train mini-GPT *từ số 0* để hiểu bản chất → Giai đoạn 1b fine-tune model open-weights để đạt chất lượng dùng thật.
- Về sau: khả năng **tự học** (Giai đoạn 3), tích hợp **Google/YouTube/Discord…** (Giai đoạn 2), và **UI kiểu Jarvis chạy nền** trên Windows (Giai đoạn 4).

Phần cứng mục tiêu: **RTX 3060 12GB, Ryzen 7 7700, 32GB RAM, Windows 11**.

## 2. Nguyên tắc làm việc với người dùng (RẤT QUAN TRỌNG)

Người dùng **mới học cả Python lẫn ML**. Vì vậy:

1. **Đưa code để họ tự gõ theo, không code hộ toàn bộ.** Khi hướng dẫn một phần mới, viết code trong file `guides/*.md` kèm giải thích từng đoạn, rồi để họ tự chép vào `src/`. Chỉ tạo sẵn file trong `src/` khi đó là *skeleton* có `# TODO` để họ điền.
2. Giải thích thuật ngữ ML lần đầu gặp (tham chiếu `docs/GLOSSARY.md`).
3. Mỗi bước phải **chạy được và kiểm chứng được** trước khi sang bước sau. Không nhảy cóc.
4. Ưu tiên **đơn giản, ít phụ thuộc**. Không thêm thư viện nếu chưa cần.
5. Trả lời bằng **tiếng Việt**.

## 3. Chuẩn code

- Python 3.11+. Format bằng `black`, lint bằng `ruff`.
- Đặt tên biến/hàm tiếng Anh, comment tiếng Việt cho phần khó.
- Type hints cho mọi hàm public.
- Mọi module trong `src/luna/` phải import được độc lập, không side-effect khi import.
- Config tập trung ở `src/luna/config.py`, KHÔNG hardcode đường dẫn/hằng số rải rác.
- Không commit weights, dataset lớn, hay secrets. Xem `.gitignore`.

## 4. Quy tắc kiểm thử

- Xem chi tiết ở `docs/TESTING.md`. Tóm tắt: **mọi PR/bước phải có test đi kèm và `pytest` phải xanh**.
- Trước khi báo "xong" một bước, chạy: `ruff check . && black --check . && pytest -q`.
- Với code training, luôn có một **"smoke test"**: chạy 1-2 step trên dữ liệu tí hon để chắc pipeline không vỡ, trước khi train thật.

## 5. Cấu trúc thư mục

```
Luna_Project/
├── CLAUDE.md            # file này
├── README.md           # tổng quan + cách bắt đầu
├── requirements.txt
├── docs/
│   ├── ROADMAP.md      # lộ trình theo giai đoạn (ĐỌC TRƯỚC)
│   ├── SKILL.md        # đặc tả "skill" của Luna
│   ├── TESTING.md      # quy tắc kiểm thử
│   └── GLOSSARY.md     # từ điển thuật ngữ ML cho người mới
├── guides/             # tutorial code để tự gõ theo
│   ├── phase1a_mini_gpt.md
│   └── phase1b_finetune.md
├── src/luna/
│   ├── config.py       # cấu hình tập trung
│   ├── core/           # model, tokenizer, training
│   ├── skills/         # kỹ năng (google, youtube, discord...)
│   └── ui/             # giao diện Jarvis
├── data/               # raw/ và processed/ (KHÔNG commit dữ liệu lớn)
├── scripts/            # script tiện ích (train.py, chat.py...)
└── tests/
```

## 6. Ranh giới an toàn

- Skill "thực thi lệnh máy tính" (mở app, gõ phím) phải chạy trong chế độ **xin xác nhận** mặc định. Không tự động hoá hành động phá huỷ (xoá file, gửi tiền, đăng bài) mà không hỏi.
- Token Discord/Google API để trong `.env`, không hardcode, không commit.
- Không thu thập/gửi dữ liệu người dùng ra ngoài trong Giai đoạn "tự học".

## 7. Khi bí

Nếu một mục tiêu (vd "chất lượng hội thoại như Neuro-sama") vượt khả năng ở bước hiện tại, **nói thẳng và đề xuất mốc thực tế hơn**, đừng hứa quá.
