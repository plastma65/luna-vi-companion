# SKILL.md — Đặc tả kỹ năng (Skill) của Luna

File này định nghĩa **skill là gì** trong Luna và **chuẩn để viết một skill mới**. Áp dụng từ Giai đoạn 2 trở đi, nhưng đọc sớm để thiết kế đúng ngay từ đầu.

## 1. Skill là gì?

Skill = một khả năng cụ thể Luna gọi ra để *làm việc với thế giới ngoài*, ví dụ: tra Google, tìm video YouTube, gửi tin Discord, mở app trên máy.

Luồng hoạt động:

```
Người dùng → Luna (model) quyết định cần skill nào
           → xuất một lệnh gọi dạng JSON: {"skill": "web_search", "args": {"query": "..."}}
           → Dispatcher (code Python) chạy skill tương ứng
           → Kết quả trả lại cho model → Luna diễn đạt thành câu trả lời tiếng Việt
```

Model **không tự chạy được gì** — nó chỉ *đề nghị*. Code Python mới thực thi. Nhờ vậy ta kiểm soát an toàn được.

## 2. Chuẩn một skill

Mỗi skill là 1 file trong `src/luna/skills/`, tuân theo interface chung:

```python
# src/luna/skills/base.py  (skeleton — bạn sẽ viết ở GĐ2)
from dataclasses import dataclass
from typing import Any

@dataclass
class SkillResult:
    ok: bool
    data: Any
    message: str = ""      # mô tả ngắn để model đọc lại

class Skill:
    name: str              # định danh duy nhất, vd "web_search"
    description: str       # 1 câu để model biết khi nào dùng
    requires_confirm: bool = False   # True nếu hành động có rủi ro

    def run(self, **args) -> SkillResult:
        raise NotImplementedError
```

### Bắt buộc với MỌI skill
1. **Tên `snake_case` duy nhất** và mô tả 1 câu (model dựa vào mô tả để chọn).
2. **Schema tham số rõ ràng** — khai báo args nào, kiểu gì.
3. **Trả về `SkillResult`**, không print lung tung, không raise ra ngoài (bắt lỗi và trả `ok=False`).
4. **`requires_confirm=True`** cho skill có rủi ro (xoá file, gửi tin ra ngoài, thao tác máy). Dispatcher sẽ hỏi người dùng trước khi chạy.
5. **Không chứa secret trong code** — token/API key đọc từ `.env`.
6. **Có test riêng** trong `tests/`, mock mạng (không gọi thật khi chạy `pytest`).

## 3. Danh mục skill dự kiến

| Skill | Mô tả | requires_confirm |
|-------|-------|------------------|
| `web_search` | Tra web (Google/DuckDuckGo), trả tiêu đề + link + tóm tắt | không |
| `youtube` | Tìm video, lấy tiêu đề/metadata, (sau) tóm tắt phụ đề | không |
| `discord_send` | Gửi tin nhắn tới kênh/DM | **có** |
| `open_app` | Mở ứng dụng Windows | **có** |
| `remember` | Lưu một sự kiện vào bộ nhớ dài hạn của Luna | không |
| `recall` | Truy hồi thông tin đã nhớ | không |

## 4. Quy tắc thêm skill mới (checklist)
- [ ] Tạo file `src/luna/skills/<name>.py` kế thừa `Skill`.
- [ ] Điền `name`, `description`, schema args, `requires_confirm`.
- [ ] Xử lý lỗi → trả `SkillResult(ok=False, ...)`, không làm sập Luna.
- [ ] Đăng ký skill vào registry (`src/luna/skills/__init__.py`).
- [ ] Viết test mock trong `tests/test_skill_<name>.py`.
- [ ] Cập nhật bảng ở §3 này.
- [ ] `pytest -q` xanh trước khi coi là xong.

## 5. Liên hệ với "self-learning" (GĐ3)
`remember` / `recall` là nền cho tự học ở mức phiên. Tự học sâu hơn (fine-tune lại từ log) được mô tả trong `docs/ROADMAP.md` §GĐ3 — KHÔNG làm ở GĐ2.
