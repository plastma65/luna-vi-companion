"""Tải tài liệu an ninh mạng CÔNG KHAI về data/knowledge/ cho RAG của Luna.

Nguồn (đều công khai / giấy phép mở):
  - OWASP Cheat Sheet Series   (CC BY-SA)  -> owasp/cheatsheets
  - OWASP Top 10 (2021)        (CC BY-SA)  -> owasp/top10
  - OWASP WSTG (Testing Guide) (CC BY-SA)  -> owasp/wstg
  - Metasploit Framework docs  (BSD-3)     -> manpages/metasploit
  - Nmap man page (nmap.org)               -> manpages/nmap

Chỉ dùng thư viện chuẩn của Python (không thêm phụ thuộc).

Cách chạy:
    python scripts/fetch_knowledge.py            # tải tất cả (bỏ qua file đã có)
    python scripts/fetch_knowledge.py --list     # xem danh sách nguồn
    python scripts/fetch_knowledge.py --only owasp-top10
    python scripts/fetch_knowledge.py --force    # tải lại, ghi đè

Lưu ý: Burp Suite / PortSwigger KHÔNG tự tải (điều khoản trang web) — anh tự lưu
tài liệu vào data/knowledge/manpages/burp/ nếu cần. OWASP WSTG đã bao phủ phần lớn
phương pháp kiểm thử web tương đương.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "data" / "knowledge"

UA = {"User-Agent": "Luna-RAG/1.0 (personal study; +local)"}
SLEEP = 0.15  # nghỉ giữa các request cho lịch sự với máy chủ
TIMEOUT = 30

# --- Nguồn lấy từ GitHub (tải đúng thư mục con, không tải cả repo) ---
GITHUB_SOURCES = [
    {
        "name": "owasp-cheatsheets",
        "repo": "OWASP/CheatSheetSeries",
        "branch": "master",
        "prefix": "cheatsheets",
        "exts": (".md",),
        "dest": "owasp/cheatsheets",
    },
    {
        "name": "owasp-top10",
        "repo": "OWASP/Top10",
        "branch": "master",
        # CHỈ lấy bản tiếng Anh: repo có 12 ngôn ngữ, nội dung trùng nhau sẽ
        # làm nhiễu chỉ mục (cùng 1 ý xuất hiện 12 lần ở 12 thứ tiếng).
        "prefix": "2021/docs/en",
        "exts": (".md",),
        "dest": "owasp/top10",
    },
    {
        "name": "owasp-wstg",
        "repo": "OWASP/wstg",
        "branch": "master",
        "prefix": "document",
        "exts": (".md",),
        "dest": "owasp/wstg",
    },
    {
        "name": "metasploit-docs",
        "repo": "rapid7/metasploit-framework",
        "branch": "master",
        "prefix": "docs",
        "exts": (".md",),
        "dest": "manpages/metasploit",
    },
]

# --- Nguồn là trang web (tải HTML rồi lọc thành text) ---
# "follow": nếu có, coi trang đầu là MỤC LỤC và tải thêm mọi link khớp mẫu này.
#   Man page nmap bị chia thành nhiều trang con man-*.html nên phải gom lại.
URL_SOURCES = [
    {
        "name": "nmap-manpage",
        "url": "https://nmap.org/book/man.html",
        "follow": r"^man-[\w-]+\.html$",
        "dest": "manpages/nmap/nmap-man.txt",
    },
]


# ====================== tiện ích mạng ======================
def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def _api(url: str) -> dict:
    return json.loads(_get(url).decode("utf-8"))


def _tree(repo: str, ref: str, recursive: bool = False) -> dict:
    url = f"https://api.github.com/repos/{repo}/git/trees/{ref}"
    if recursive:
        url += "?recursive=1"
    return _api(url)


# ====================== HTML -> text ======================
class _HtmlToText(HTMLParser):
    """Bóc thẻ HTML, giữ lại phần chữ (bỏ script/style)."""

    _BREAK = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "pre"}

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):  # noqa: D102
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in self._BREAK:
            self._parts.append("\n")

    def handle_endtag(self, tag):  # noqa: D102
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):  # noqa: D102
        if not self._skip:
            self._parts.append(data)

    def text(self) -> str:
        t = "".join(self._parts)
        t = re.sub(r"[ \t]{2,}", " ", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()


def html_to_text(html: str) -> str:
    p = _HtmlToText()
    p.feed(html)
    return p.text()


# ====================== tải từ GitHub ======================
def _resolve_root_tree(repo: str, branch: str) -> tuple[str, dict]:
    """Trả (tên nhánh dùng được, cây thư mục gốc). Tự thử master/main."""
    tried = [branch] + [b for b in ("main", "master") if b != branch]
    last: Exception | None = None
    for b in tried:
        try:
            return b, _tree(repo, b)
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (404, 422):
                raise
    raise RuntimeError(f"Không mở được repo {repo} (nhánh đã thử: {tried}) — {last}")


def _list_repo_files(src: dict) -> tuple[str, list[str]]:
    """Trả (nhánh, danh sách đường dẫn file) trong thư mục con cần lấy."""
    branch, cur = _resolve_root_tree(src["repo"], src["branch"])
    parts = [p for p in src["prefix"].strip("/").split("/") if p]
    for part in parts:
        entry = next((e for e in cur["tree"] if e["path"] == part and e["type"] == "tree"), None)
        if entry is None:
            raise RuntimeError(f"{src['repo']}: không thấy thư mục '{src['prefix']}'")
        time.sleep(SLEEP)
        cur = _tree(src["repo"], entry["sha"])
    time.sleep(SLEEP)
    sub = _tree(src["repo"], cur["sha"], recursive=True)
    files = [
        e["path"]
        for e in sub["tree"]
        if e["type"] == "blob" and e["path"].lower().endswith(tuple(src["exts"]))
    ]
    return branch, sorted(files)


def fetch_github(src: dict, force: bool) -> int:
    print(f"\n=== {src['name']} — {src['repo']}/{src['prefix']} ===")
    branch, files = _list_repo_files(src)
    print(f"Tìm thấy {len(files)} file. Đang tải...")
    out_root = KNOWLEDGE_DIR / src["dest"]
    saved = 0
    for i, rel in enumerate(files, 1):
        dest = out_root / rel
        if dest.exists() and not force:
            continue
        raw = (
            f"https://raw.githubusercontent.com/{src['repo']}/{branch}/"
            f"{src['prefix'].strip('/')}/{rel}"
        )
        try:
            data = _get(raw)
        except Exception as e:  # noqa: BLE001
            print(f"  [bỏ qua] {rel}: {e}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        saved += 1
        if saved % 25 == 0 or i == len(files):
            print(f"  ...{saved} file đã lưu")
        time.sleep(SLEEP)
    print(f"✅ {src['name']}: lưu {saved} file mới vào {out_root}")
    return saved


def _links(html: str, pattern: str) -> list[str]:
    """Lấy các href khớp mẫu, giữ thứ tự và bỏ trùng."""
    found = re.findall(r'href=["\']([^"\'#?]+)', html)
    out: list[str] = []
    for h in found:
        name = h.rsplit("/", 1)[-1]
        if re.search(pattern, name) and h not in out:
            out.append(h)
    return out


def fetch_url(src: dict, force: bool) -> int:
    print(f"\n=== {src['name']} — {src['url']} ===")
    dest = KNOWLEDGE_DIR / src["dest"]
    if dest.exists() and not force:
        print("Đã có sẵn, bỏ qua (dùng --force để tải lại).")
        return 0

    html = _get(src["url"]).decode("utf-8", errors="replace")
    parts = [html_to_text(html)]

    # Trang mục lục -> tải thêm từng trang con
    pattern = src.get("follow")
    if pattern:
        subs = _links(html, pattern)
        print(f"Trang mục lục có {len(subs)} trang con. Đang tải...")
        for i, href in enumerate(subs, 1):
            url = urllib.parse.urljoin(src["url"], href)
            try:
                sub_html = _get(url).decode("utf-8", errors="replace")
            except Exception as e:  # noqa: BLE001
                print(f"  [bỏ qua] {href}: {e}")
                continue
            parts.append(f"\n\n===== {href} =====\n{html_to_text(sub_html)}")
            if i % 10 == 0 or i == len(subs):
                print(f"  ...{i}/{len(subs)} trang")
            time.sleep(SLEEP)

    text = "\n".join(parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"✅ Lưu {len(text):,} ký tự vào {dest}")
    return 1


# ====================== ghi chú nguồn (để trích dẫn) ======================
def write_sources_note() -> None:
    note = KNOWLEDGE_DIR / "SOURCES.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "# Nguồn tài liệu trong kho tri thức của Luna\n\n"
        "Tải tự động bằng `scripts/fetch_knowledge.py`.\n\n"
        "| Thư mục | Nguồn | Giấy phép |\n"
        "|---|---|---|\n"
        "| owasp/cheatsheets | OWASP Cheat Sheet Series | CC BY-SA 4.0 |\n"
        "| owasp/top10 | OWASP Top 10 (2021) | CC BY-SA 4.0 |\n"
        "| owasp/wstg | OWASP Web Security Testing Guide | CC BY-SA 4.0 |\n"
        "| manpages/metasploit | Metasploit Framework docs | BSD-3-Clause |\n"
        "| manpages/nmap | Nmap man page (nmap.org) | Tài liệu công khai |\n"
        "| books/ | Sách anh tự thêm | **Chỉ thêm tài liệu anh có quyền dùng** |\n"
        "| manpages/burp/ | Burp/PortSwigger — tự thêm thủ công | Theo điều khoản của họ |\n",
        encoding="utf-8",
    )
    print(f"\n📝 Đã ghi chú nguồn vào {note}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Tải tài liệu bảo mật công khai cho RAG của Luna")
    ap.add_argument("--only", help="chỉ tải 1 nguồn (xem --list)")
    ap.add_argument("--force", action="store_true", help="tải lại, ghi đè file đã có")
    ap.add_argument("--list", action="store_true", help="liệt kê các nguồn")
    args = ap.parse_args()

    all_srcs = [(s["name"], "github", s) for s in GITHUB_SOURCES]
    all_srcs += [(s["name"], "url", s) for s in URL_SOURCES]

    if args.list:
        print("Các nguồn có sẵn:")
        for name, kind, s in all_srcs:
            print(f"  - {name:22s} ({kind})  -> data/knowledge/{s['dest']}")
        return 0

    todo = [x for x in all_srcs if not args.only or x[0] == args.only]
    if not todo:
        print(f"Không có nguồn tên '{args.only}'. Dùng --list để xem.")
        return 1

    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, kind, s in todo:
        try:
            total += fetch_github(s, args.force) if kind == "github" else fetch_url(s, args.force)
        except Exception as e:  # noqa: BLE001
            print(f"❌ {name}: {e}")

    write_sources_note()
    print(f"\n🌙 Xong. Tổng cộng {total} file mới trong {KNOWLEDGE_DIR}")
    print("Bước tiếp theo: dựng chỉ mục (R2) — mình sẽ viết scripts/build_index.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
