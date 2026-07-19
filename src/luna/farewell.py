"""Nhận biết lời tạm biệt — dùng CHUNG cho cả 3 chế độ của Luna.

Vì sao tách riêng:
  - Trước đây mỗi script có danh sách riêng, sửa 1 chỗ quên 2 chỗ.
  - Chế độ giọng nói KHÔNG nên bắt người dùng phải nói đúng tên "Luna" —
    STT rất hay nghe sai tên riêng.

Cẩn trọng: ở chế độ nói, chỉ "tạm biệt" mới thoát. KHÔNG dùng mỗi chữ "thoát",
vì câu hỏi bảo mật rất hay có nó ("cách thoát khỏi sandbox", "thoát quyền root")
— sẽ tắt Luna oan.
"""

from __future__ import annotations

import unicodedata

# Cụm chào tạm biệt — áp dụng cho MỌI chế độ (gõ chữ lẫn nói)
FAREWELL_PHRASES = ("tạm biệt", "tam biet", "kết thúc trò chuyện", "ket thuc tro chuyen")

# Lệnh thoát khi GÕ CHỮ — phải khớp cả câu, tránh dính vào câu hỏi bình thường
TYPED_EXIT_WORDS = {"thoát", "thoat", "quit", "exit", "bye", "q"}

# Lời chào của Luna lúc tắt
GOODBYE_TEXT = "Dạ tạm biệt anh nhé, hẹn gặp lại anh."  # bản để ĐỌC
GOODBYE_DISPLAY = "Dạ tạm biệt anh nhé, hẹn gặp lại anh 🌙"  # bản để IN


def _nfc(s: str) -> str:
    """Chuẩn hoá Unicode — tiếng Việt có 2 cách mã hoá dấu, không chuẩn hoá sẽ so sai."""
    return unicodedata.normalize("NFC", s)


def is_farewell(text: str, typed: bool = False) -> bool:
    """True nếu người dùng đang chào tạm biệt.

    typed=True  -> chế độ gõ chữ, chấp nhận thêm 'thoát'/'quit'/'exit' (khớp cả câu)
    typed=False -> chế độ nói, chỉ chấp nhận cụm 'tạm biệt'
    """
    t = _nfc(text).strip().lower().strip(" .!?,")
    if not t:
        return False
    if any(p in t for p in FAREWELL_PHRASES):
        return True
    return typed and t in TYPED_EXIT_WORDS
