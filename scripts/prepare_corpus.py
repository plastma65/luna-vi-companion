"""Tải & gộp văn bản tiếng Việt public (Wikipedia, CC-BY-SA) thành corpus.txt.

Dùng cho Giai đoạn 1a (mini-GPT). Chỉ dùng thư viện CHUẨN của Python
(urllib, json) nên KHÔNG cần cài thêm gì.

Chạy:
    python scripts/prepare_corpus.py

Kết quả: data/raw/corpus.txt (~1-2 MB text tiếng Việt sạch).
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Thư mục đích (data/raw/ nằm cạnh thư mục scripts/)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "corpus.txt"

API = "https://vi.wikipedia.org/w/api.php"
# User-Agent lịch sự theo yêu cầu của Wikipedia
HEADERS = {"User-Agent": "LunaProject/0.1 (hoc tap; lien he: local)"}

# Danh sách chủ đề lớn -> mỗi bài cho vài nghìn tới vài chục nghìn chữ.
# Bạn có thể thêm/bớt tuỳ ý để đổi "khẩu vị" dữ liệu.
TITLES = [
    "Việt Nam",
    "Hà Nội",
    "Thành phố Hồ Chí Minh",
    "Lịch sử Việt Nam",
    "Văn hóa Việt Nam",
    "Ẩm thực Việt Nam",
    "Tiếng Việt",
    "Địa lý Việt Nam",
    "Nhà Nguyễn",
    "Nhà Lý",
    "Nhà Trần",
    "Nhà Lê sơ",
    "Chiến tranh Việt Nam",
    "Hùng Vương",
    "Hai Bà Trưng",
    "Ngô Quyền",
    "Lý Thái Tổ",
    "Trần Hưng Đạo",
    "Nguyễn Trãi",
    "Nguyễn Du",
    "Truyện Kiều",
    "Hồ Xuân Hương",
    "Âm nhạc Việt Nam",
    "Bóng đá Việt Nam",
    "Giáo dục Việt Nam",
    "Kinh tế Việt Nam",
    "Phật giáo",
    "Nho giáo",
    "Tết Nguyên Đán",
    "Áo dài",
    "Sông Hồng",
    "Sông Cửu Long",
    "Vịnh Hạ Long",
    "Huế",
    "Đà Nẵng",
    "Hải Phòng",
    "Cần Thơ",
    "Tây Nguyên",
    "Đồng bằng sông Cửu Long",
    "Khí hậu Việt Nam",
    "Động vật",
    "Thực vật",
    "Vũ trụ",
    "Trái Đất",
    "Mặt Trời",
    "Nước",
    "Máy tính",
    "Internet",
    "Trí tuệ nhân tạo",
    "Toán học",
    "Vật lý học",
    "Hóa học",
    "Sinh học",
    "Lịch sử thế giới",
]


def fetch_extract(title: str) -> str:
    """Lấy nội dung text thuần của 1 bài Wikipedia qua API."""
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",  # trả text thuần, bỏ HTML
        "redirects": "1",
        "format": "json",
        "titles": title,
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    pages = data.get("query", {}).get("pages", {})
    parts = []
    for page in pages.values():
        text = page.get("extract", "")
        if text:
            parts.append(text)
    return "\n".join(parts)


def clean(text: str) -> str:
    """Làm sạch nhẹ: bỏ dòng trống thừa và tiêu đề mục '== ... =='."""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("==") and s.endswith("=="):  # bỏ dòng tiêu đề mục
            continue
        lines.append(s)
    return "\n".join(lines)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    total = 0
    for i, title in enumerate(TITLES, 1):
        try:
            raw = fetch_extract(title)
            text = clean(raw)
        except Exception as e:  # noqa: BLE001
            print(f"  [bỏ qua] {title}: {e}")
            continue
        if text:
            chunks.append(text)
            total += len(text)
        print(f"[{i:2d}/{len(TITLES)}] {title:35s} | tổng {total/1e6:.2f} MB")
        time.sleep(0.3)  # lịch sự với server, tránh bị chặn

    corpus = "\n\n".join(chunks)
    OUT.write_text(corpus, encoding="utf-8")
    print(f"\nĐã lưu {OUT}")
    print(f"Dung lượng: {len(corpus)/1e6:.2f} MB | Ký tự khác nhau: {len(set(corpus))}")
    if len(corpus) < 200_000:
        print("CẢNH BÁO: corpus hơi nhỏ, cân nhắc thêm bài vào TITLES.", file=sys.stderr)


if __name__ == "__main__":
    main()
