"""Skill cơ bản của Luna + bộ định tuyến lệnh (intent router).

Ý tưởng: quét câu người dùng tìm mẫu lệnh; nếu khớp thì chạy skill (Python)
và trả về câu xác nhận bằng giọng Luna. Nếu không khớp -> trả None để Luna
trò chuyện bình thường.

An toàn: các skill ở đây chỉ MỞ app/trang web và XEM giờ — không xoá, không
gửi gì ra ngoài. Skill có rủi ro (đăng bài, xoá file...) sẽ cần xin xác nhận.
"""

from __future__ import annotations

import datetime
import os
import re
import urllib.parse
import webbrowser

THU = ["thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu", "thứ Bảy", "Chủ Nhật"]


def now_datetime() -> str:
    now = datetime.datetime.now()
    return (
        f"Dạ bây giờ là {now.hour} giờ {now.minute:02d} phút, "
        f"{THU[now.weekday()]}, ngày {now.day} tháng {now.month} năm {now.year} ạ 🕐"
    )


def open_google() -> str:
    webbrowser.open("https://www.google.com")
    return "Dạ em mở Google cho anh rồi nha 🌐"


def open_youtube() -> str:
    webbrowser.open("https://www.youtube.com")
    return "Dạ em mở YouTube cho anh rồi nha 🎬"


def open_discord() -> str:
    try:
        os.startfile("discord://")  # mở app Discord nếu đã cài
    except Exception:  # noqa: BLE001
        webbrowser.open("https://discord.com/app")  # nếu không có app thì mở web
    return "Dạ em mở Discord cho anh rồi ạ 💬"


def search_google(query: str) -> str:
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(query))
    return f"Dạ em tìm '{query}' trên Google cho anh nha 🔎"


def search_youtube(query: str) -> str:
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
    return f"Dạ em tìm '{query}' trên YouTube cho anh nha 🎬"


# Các từ khoá cần loại bỏ để lấy ra "nội dung cần tìm"
_STRIP = [
    "tìm kiếm",
    "tìm giúp em",
    "tìm giúp anh",
    "tìm giúp",
    "tìm hộ",
    "tìm",
    "kiếm",
    "mở",
    "giúp anh",
    "giúp em",
    "cho anh",
    "cho em",
    "trên",
    "về",
    "thông tin",
    "dùm",
    "giùm",
    "luna",
    "ơi",
    "nha",
    "nhé",
    "đi",
    "với",
]


def _extract_query(text: str, extra: list[str]) -> str:
    q = text
    for w in _STRIP + extra:
        q = q.replace(w, " ")
    q = re.sub(r"\s+", " ", q).strip(" ,.?!")
    return q if len(q) >= 2 else ""


# Các cách Whisper hay nghe nhầm tên tiếng Anh
YOUTUBE_WORDS = ["youtube", "diu túp", "du túp", "iu túp", "youtub", "yout"]
GOOGLE_WORDS = ["google", "gu gồ", "gu gờ", "gút gồ", "gu gô", "gồ gồ"]
DISCORD_WORDS = ["discord", "đít co", "đít cọt", "đi cô", "đi cợt", "đít-co", "đis co"]


def route(text: str) -> str | None:
    """Trả câu xác nhận (Luna nói) nếu là lệnh; None nếu là trò chuyện thường."""
    t = text.lower().strip()

    # 1) Ngày giờ
    if any(
        k in t
        for k in [
            "mấy giờ",
            "giờ rồi",
            "ngày mấy",
            "thứ mấy",
            "bây giờ là mấy",
            "ngày bao nhiêu",
            "hôm nay là ngày",
        ]
    ):
        return now_datetime()

    # 2) YouTube (kiểm trước Google vì câu có thể chứa cả 'tìm')
    if any(w in t for w in YOUTUBE_WORDS):
        q = _extract_query(t, YOUTUBE_WORDS)
        return search_youtube(q) if q else open_youtube()

    # 3) Discord
    if any(w in t for w in DISCORD_WORDS):
        return open_discord()

    # 4) Google / tìm kiếm chung
    if any(w in t for w in GOOGLE_WORDS) or "tìm" in t or "kiếm" in t:
        q = _extract_query(t, GOOGLE_WORDS)
        return search_google(q) if q else open_google()

    return None
