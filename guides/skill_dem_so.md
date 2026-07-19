# Skill: Đếm số (Luna đếm chính xác)

Model Luna giỏi trò chuyện nhưng hay "làm biếng" khi phải liệt kê (đếm 1→20 thì
viết tắt "1, 2, 3, … 20"). Cách khắc phục đúng tinh thần dự án: **để code lo tác
vụ, model lo trò chuyện**. Ta thêm một skill: khi anh nói "đếm từ X đến Y", Python
tự sinh dãy số thật rồi cho Luna đọc.

File cần sửa: `src/luna/skills/commands.py`.

---

## Bước 1 — Thêm bộ chuyển "chữ số tiếng Việt → số"

Voice mode đôi khi cho ra chữ ("hai mươi") thay vì "20", nên ta cần hàm đọc hiểu cả
hai. Chép đoạn này vào `commands.py`, **ngay trên** hàm `route(...)`:

```python
# ====== Skill ĐẾM SỐ ======
# Bảng chữ số đơn (gồm cả biến thể: tư=4, lăm=5, mốt=1 khi ghép hàng chục)
_UNIT = {
    "không": 0, "một": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5,
    "lăm": 5, "sáu": 6, "bảy": 7, "tám": 8, "chín": 9, "mốt": 1,
}


def _words_to_int(s: str) -> int | None:
    """Đổi '20' hoặc 'hai mươi' -> 20. Hỗ trợ 0..99. Không hiểu -> None."""
    s = s.strip().lower()
    if s.isdigit():
        return int(s)
    if s in _UNIT:
        return _UNIT[s]
    if s == "mười":
        return 10
    m = re.match(r"mười\s+(\S+)$", s)                 # 11..19: "mười ba"
    if m and m.group(1) in _UNIT:
        return 10 + _UNIT[m.group(1)]
    m = re.match(r"(\S+)\s+mươi(?:\s+(\S+))?$", s)     # 20..99: "hai mươi mốt"
    if m and m.group(1) in _UNIT:
        return _UNIT[m.group(1)] * 10 + (_UNIT[m.group(2)] if m.group(2) in _UNIT else 0)
    return None


def _num_from_start(s: str) -> int | None:
    """Lấy số dài nhất ở ĐẦU chuỗi, bỏ đuôi thừa ('nhé', 'nha', 'giúp em'...)."""
    toks = s.split()
    for n in (3, 2, 1):          # thử 3 từ ('hai mươi mốt'), rồi 2, rồi 1
        if len(toks) >= n:
            v = _words_to_int(" ".join(toks[:n]))
            if v is not None:
                return v
    return None
```

Giải thích:
- `_UNIT`: từ điển chữ → số. Có `tư`/`lăm`/`mốt` vì tiếng Việt đổi âm khi ghép
  (21 = "hai mươi **mốt**", 25 = "hai mươi **lăm**").
- `_words_to_int`: xử lý 3 dạng — số đơn, "mười X" (11–19), "X mươi Y" (20–99).
- `_num_from_start`: câu nói thường có đuôi ("đếm đến 10 **nhé**"). Hàm này thử ghép
  3→2→1 từ đầu, lấy cụm nào ra số hợp lệ thì dừng — nên "10 nhé" vẫn ra 10.

---

## Bước 2 — Hàm đếm chính

Chép tiếp, ngay dưới `_num_from_start`:

```python
MAX_COUNT = 200   # chặn "đếm từ 1 đến 1 tỷ" làm Luna đọc mãi


def count_range(text: str) -> str | None:
    """'đếm từ X đến Y' -> câu Luna đọc dãy số thật. Không phải lệnh đếm -> None."""
    t = text.lower().strip()
    if "đếm" not in t and "đọc số" not in t:
        return None
    reverse = ("ngược" in t) or ("giảm dần" in t)

    m = re.search(r"từ\s+(.+?)\s+(?:đến|tới|->|về)\s+(.+)$", t)
    if m:                                   # "đếm từ X đến Y"
        a, b = _num_from_start(m.group(1)), _num_from_start(m.group(2))
    else:                                   # "đếm đến Y" (mặc định từ 1)
        m2 = re.search(r"(?:đếm|đọc số)(?:\s+ngược)?(?:\s+(?:đến|tới))?\s+(.+)$", t)
        a, b = 1, (_num_from_start(m2.group(1)) if m2 else None)

    if a is None or b is None:
        return None
    if a > b:
        a, b = b, a
    if b - a + 1 > MAX_COUNT:
        return f"Dạ nhiều quá, em chỉ đếm được tối đa {MAX_COUNT} số một lần thôi ạ."

    if reverse:
        seq = ", ".join(str(n) for n in range(b, a - 1, -1))
        return f"Dạ em đếm ngược từ {b} về {a} nè: {seq}. Xong rồi ạ 🌙"
    seq = ", ".join(str(n) for n in range(a, b + 1))
    return f"Dạ em đếm từ {a} đến {b} nè: {seq}. Xong rồi ạ 🌙"
```

Giải thích:
- Chỉ chạy khi câu có "đếm"/"đọc số" → không đụng các câu khác.
- Regex 1 bắt "từ … đến/tới/về …". Nếu không có "từ", regex 2 bắt "đếm đến Y" và
  mặc định bắt đầu từ 1.
- `a > b` thì hoán đổi cho an toàn; `MAX_COUNT` chặn dãy quá dài.
- Trả về **chuỗi số cách nhau bằng dấu phẩy** — bộ đọc số trong TTS sẽ tự đổi
  "1, 2, 3" thành "một, hai, ba", dấu phẩy tạo nhịp ngắt tự nhiên.

---

## Bước 3 — Gắn vào router

Trong hàm `route(...)`, thêm **ngay sau dòng** `t = text.lower().strip()` và
**trước** mục "1) Ngày giờ":

```python
    # 0) Đếm số (đặt sớm để không lẫn với "tìm kiếm")
    dem = count_range(t)
    if dem:
        return dem
```

Đặt sớm để câu "đếm…" không bị nhánh tìm kiếm/khác cướp mất.

---

## Bước 4 — Viết test (bắt buộc theo quy tắc dự án)

Tạo file `tests/test_skill_dem.py`:

```python
from luna.skills.commands import count_range


def test_dem_xuoi():
    r = count_range("đếm từ 1 đến 5")
    assert r is not None and "1, 2, 3, 4, 5" in r


def test_dem_mac_dinh_tu_1():
    assert "1, 2, 3" in count_range("đếm đến 3")


def test_dem_bang_chu():
    assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10" in count_range("đếm từ một đến mười")


def test_dem_nguoc():
    assert "5, 4, 3, 2, 1" in count_range("đếm ngược từ 5 về 1")


def test_duoi_thua():
    assert "1, 2, 3, 4, 5, 6, 7, 8, 9, 10" in count_range("Luna đếm từ 1 tới 10 nhé")


def test_khong_phai_lenh_dem():
    assert count_range("hôm nay trời đẹp không") is None


def test_gioi_han():
    assert "tối đa" in count_range("đếm từ 1 đến 999")
```

Chạy kiểm tra:

```
D:\Luna_Project\.venv\Scripts\activate
cd D:\Luna_Project
ruff check . && black --check . && pytest -q
```

Xanh hết là xong. Rồi mở `Luna_ChatVoice.bat`, gõ **"đếm từ 1 đến 20"** — giờ Luna
đọc đủ 20 số thật, không tắt ngang nữa.

---

## Giới hạn & mở rộng
- Hiện hỗ trợ số **0–99** khi nói bằng chữ; nói bằng **chữ số** ("từ 1 đến 300")
  thì không giới hạn (trừ `MAX_COUNT`).
- Muốn đếm bước nhảy ("đếm 2, 4, 6…") thì thêm bắt "bước"/"cách" và dùng `range(a, b+1, step)`.
- Đây là mẫu chung cho các skill "tác vụ tính toán" — sau này làm skill khác
  (đổi đơn vị, tính tuổi…) cứ theo khuôn: nhận diện câu → tính bằng Python → trả câu Luna nói.
```
