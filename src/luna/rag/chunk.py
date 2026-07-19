"""Đọc tài liệu trong data/knowledge -> cắt thành các 'chunk' kèm nguồn."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from luna.config import RAG, KNOWLEDGE_DIR

TEXT_EXTS = {".md", ".markdown", ".txt"}
PDF_EXTS = {".pdf"}

# File điều hướng/ghi chú, không phải kiến thức -> không đưa vào chỉ mục
SKIP_NAMES = {"sources.md", "readme.md", "index.md", "license.md", "contributing.md"}


@dataclass
class Chunk:
    """Một mẩu tài liệu + nguồn gốc để trích dẫn."""

    text: str  # nội dung
    source: str  # đường dẫn tương đối, vd 'owasp/cheatsheets/XSS...md'
    title: str  # 'Tên tài liệu › Tiêu đề mục'


def read_text(path: Path) -> str:
    """Đọc .md/.txt trực tiếp; .pdf thì bóc chữ bằng pypdf."""
    if path.suffix.lower() in PDF_EXTS:
        from pypdf import PdfReader

        return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="replace")


def clean(text: str) -> str:
    """Bỏ rác markdown để chunk đỡ nhiễu."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)  # front-matter YAML
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # ảnh
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # link -> giữ chữ, bỏ URL
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --- Nhận diện tiêu đề ---
# Markdown: '## Tiêu đề'
_MD_HEADING = re.compile(r"^(#{1,4})\s+(.*)")
# Man page: dòng định nghĩa tuỳ chọn, vd '-sS (TCP SYN scan)', '-iL <file> (Input from list)'
_MAN_OPTION = re.compile(
    r"^\s*(-{1,2}[A-Za-z0-9][\w-]*(?:\s*[<\[][^()]*?[>\]])?)\s*\(([^()]{3,70})\)\s*$"
)
# Man page: tiêu đề mục viết HOA, vd 'HOST DISCOVERY', 'SCAN TECHNIQUES'
_MAN_SECTION = re.compile(r"^\s*([A-Z][A-Z0-9 /,&'-]{3,50}):?\s*$")


def split_sections(text: str, markdown: bool = True) -> list[tuple[str, str]]:
    """Cắt theo tiêu đề -> [(tiêu đề, nội dung)].

    QUAN TRỌNG: chỉ coi '#' là heading với file .md. Trong man page/.txt, '#' là
    dấu nhắc shell của root (vd '# nmap -A -T4 ...') — nhận nhầm sẽ gom cả file
    thành 1 mục khổng lồ và phá nát chất lượng tìm kiếm.
    """
    out: list[tuple[str, str]] = []
    title, buf = "(mở đầu)", []
    for line in text.split("\n"):
        new: str | None = None
        if markdown:
            m = _MD_HEADING.match(line)
            if m:
                new = m.group(2).strip()
        else:
            m = _MAN_OPTION.match(line)
            if m:
                new = f"{m.group(1).strip()} ({m.group(2).strip()})"
            else:
                m = _MAN_SECTION.match(line)
                if m:
                    new = m.group(1).strip()
        if new:
            if buf:
                out.append((title, "\n".join(buf).strip()))
            title, buf = new, []
        else:
            buf.append(line)
    if buf:
        out.append((title, "\n".join(buf).strip()))
    return [(t, b) for t, b in out if b]


# Giữ tên cũ để code/test cũ không vỡ
def split_by_heading(text: str) -> list[tuple[str, str]]:
    """(cũ) Cắt theo tiêu đề markdown."""
    return split_sections(text, markdown=True)


def split_long(text: str, size: int, overlap: int) -> list[str]:
    """Mục quá dài -> cắt tiếp theo ranh giới đoạn văn, có gối đầu (overlap)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    cur = ""
    for p in paras:
        while len(p) > size:  # đoạn khổng lồ -> cắt cứng
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(p[:size])
            p = p[size - overlap :]
        if len(cur) + len(p) + 2 <= size:
            cur = f"{cur}\n\n{p}" if cur else p
        else:
            chunks.append(cur)
            cur = (cur[-overlap:] + "\n\n" + p) if overlap else p
    if cur:
        chunks.append(cur)
    return chunks


def chunk_file(path: Path, root: Path) -> list[Chunk]:
    try:
        text = clean(read_text(path))
    except Exception as e:  # noqa: BLE001
        print(f"  [bỏ qua] {path.name}: {e}")
        return []
    if not text:
        return []
    source = path.relative_to(root).as_posix()
    doc = path.stem.replace("_", " ")
    is_md = path.suffix.lower() in {".md", ".markdown"}
    out: list[Chunk] = []
    for heading, body in split_sections(text, markdown=is_md):
        for piece in split_long(body, RAG.chunk_size, RAG.chunk_overlap):
            piece = piece.strip()
            if len(piece) < RAG.min_chunk:  # quá ngắn -> rác
                continue
            out.append(Chunk(text=piece, source=source, title=f"{doc} › {heading}"))
    return out


def iter_files(root: Path | None = None):
    root = root or KNOWLEDGE_DIR
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXTS | PDF_EXTS:
            continue
        if p.name.lower() in SKIP_NAMES:  # file điều hướng/ghi chú -> bỏ
            continue
        yield p


def build_chunks(root: Path | None = None) -> list[Chunk]:
    root = root or KNOWLEDGE_DIR
    out: list[Chunk] = []
    for p in iter_files(root):
        out.extend(chunk_file(p, root))
    return out
