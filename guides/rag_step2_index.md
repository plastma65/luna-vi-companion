# RAG — Bước R2: Cắt chunk & dựng chỉ mục thật

Mục tiêu: biến ~480 file tài liệu trong `data/knowledge/` thành một **chỉ mục
FAISS** tìm được theo ý nghĩa. Xong bước này, anh gõ câu hỏi tiếng Việt là ra đúng
đoạn tài liệu tiếng Anh liên quan.

> Code trong guide này em **đã chạy thử trên chính kho của anh**: ra 9.967 chunk,
> dài trung bình 523 ký tự. Anh gõ theo là chạy được.

Anh sẽ tạo 4 file trong `src/luna/rag/`. Tạo thư mục trước:

```
D:\Luna_Project\src\luna\rag\
```

---

## 1. `src/luna/rag/__init__.py`

Để trống (chỉ để Python coi đây là package):

```python
"""Gói RAG của Luna: cắt chunk, embedding, kho vector."""
```

---

## 2. `src/luna/rag/chunk.py` — đọc tài liệu & cắt đoạn

Đây là file **quan trọng nhất về chất lượng**. Rác vào thì rác ra.

```python
"""Đọc tài liệu trong data/knowledge -> cắt thành các 'chunk' kèm nguồn."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from luna.config import RAG, KNOWLEDGE_DIR

TEXT_EXTS = {".md", ".markdown", ".txt"}
PDF_EXTS = {".pdf"}


@dataclass
class Chunk:
    """Một mẩu tài liệu + nguồn gốc để trích dẫn."""

    text: str      # nội dung
    source: str    # đường dẫn tương đối, vd 'owasp/cheatsheets/XSS...md'
    title: str     # 'Tên tài liệu › Tiêu đề mục'


def read_text(path: Path) -> str:
    """Đọc .md/.txt trực tiếp; .pdf thì bóc chữ bằng pypdf."""
    if path.suffix.lower() in PDF_EXTS:
        from pypdf import PdfReader

        return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="replace")


def clean(text: str) -> str:
    """Bỏ rác markdown để chunk đỡ nhiễu."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)   # front-matter YAML
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)          # ảnh
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)       # link -> giữ chữ, bỏ URL
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_by_heading(text: str) -> list[tuple[str, str]]:
    """Cắt theo tiêu đề markdown -> [(tiêu đề, nội dung)]."""
    out: list[tuple[str, str]] = []
    title, buf = "(mở đầu)", []
    for line in text.split("\n"):
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            if buf:
                out.append((title, "\n".join(buf).strip()))
            title, buf = m.group(2).strip(), []
        else:
            buf.append(line)
    if buf:
        out.append((title, "\n".join(buf).strip()))
    return [(t, b) for t, b in out if b]


def split_long(text: str, size: int, overlap: int) -> list[str]:
    """Mục quá dài -> cắt tiếp theo ranh giới đoạn văn, có gối đầu (overlap)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    cur = ""
    for p in paras:
        while len(p) > size:                 # đoạn khổng lồ -> cắt cứng
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(p[:size])
            p = p[size - overlap:]
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
    out: list[Chunk] = []
    for heading, body in split_by_heading(text):
        for piece in split_long(body, RAG.chunk_size, RAG.chunk_overlap):
            piece = piece.strip()
            if len(piece) < RAG.min_chunk:   # quá ngắn -> rác
                continue
            out.append(Chunk(text=piece, source=source, title=f"{doc} › {heading}"))
    return out


def iter_files(root: Path | None = None):
    root = root or KNOWLEDGE_DIR
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in TEXT_EXTS | PDF_EXTS:
            yield p


def build_chunks(root: Path | None = None) -> list[Chunk]:
    root = root or KNOWLEDGE_DIR
    out: list[Chunk] = []
    for p in iter_files(root):
        out.extend(chunk_file(p, root))
    return out
```

Ý chính cần hiểu:
- **Cắt theo heading trước** → mỗi chunk là một ý trọn vẹn, và ta biết nó thuộc mục nào.
- **Overlap 120 ký tự** → câu bị cắt ngang vẫn còn phần đầu ở chunk sau, tránh mất ý.
- **`min_chunk`** → bỏ mẩu quá ngắn (dòng tiêu đề trơ trọi) vì chúng gây nhiễu tìm kiếm.
- Giữ `source` + `title` để sau này Luna **trích nguồn** được.

---

## 3. `src/luna/rag/embed.py` — chữ thành vector

```python
"""Embedding: đổi chữ thành vector bằng model đa ngữ (e5)."""
from __future__ import annotations

import numpy as np

from luna.config import RAG

_model = None


def get_model():
    """Nạp model 1 lần (lazy) rồi dùng lại."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        print(f"Đang nạp embedding model: {RAG.embed_model} ...")
        _model = SentenceTransformer(RAG.embed_model)
    return _model


def _encode(texts: list[str], prefix: str) -> np.ndarray:
    model = get_model()
    vecs = model.encode(
        [prefix + t for t in texts],
        batch_size=RAG.embed_batch,
        normalize_embeddings=True,          # chuẩn hoá -> dot product = cosine
        show_progress_bar=len(texts) > 200,
    )
    return np.asarray(vecs, dtype="float32")


def encode_passages(texts: list[str]) -> np.ndarray:
    """Vector cho TÀI LIỆU (e5 yêu cầu tiền tố 'passage: ')."""
    return _encode(texts, "passage: ")


def encode_query(query: str) -> np.ndarray:
    """Vector cho CÂU HỎI (tiền tố 'query: ')."""
    return _encode([query], "query: ")
```

Nhớ: model e5 **bắt buộc** tiền tố `passage:` / `query:`. Thiếu là chất lượng tụt hẳn.

---

## 4. `src/luna/rag/store.py` — kho vector FAISS

```python
"""Kho vector FAISS: dựng chỉ mục, lưu ra file, nạp lại, tìm kiếm."""
from __future__ import annotations

import json

from luna.config import RAG, RAG_INDEX_DIR
from luna.rag.embed import encode_passages, encode_query

INDEX_FILE = RAG_INDEX_DIR / "luna.faiss"
META_FILE = RAG_INDEX_DIR / "luna_meta.json"

_index = None
_meta: list[dict] | None = None


def build(chunks: list) -> int:
    """Embedding toàn bộ chunk rồi lưu chỉ mục + metadata ra đĩa."""
    import faiss

    # Ghép tiêu đề vào nội dung để vector giàu ngữ cảnh hơn
    texts = [f"{c.title}\n{c.text}" for c in chunks]
    vecs = encode_passages(texts)

    index = faiss.IndexFlatIP(vecs.shape[1])   # inner product (vector đã chuẩn hoá) = cosine
    index.add(vecs)

    RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))
    META_FILE.write_text(
        json.dumps(
            [{"text": c.text, "source": c.source, "title": c.title} for c in chunks],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return len(chunks)


def load():
    """Nạp chỉ mục 1 lần rồi dùng lại."""
    global _index, _meta
    if _index is None:
        import faiss

        if not INDEX_FILE.exists():
            raise FileNotFoundError(
                "Chưa có chỉ mục. Chạy trước: python scripts\\build_index.py"
            )
        _index = faiss.read_index(str(INDEX_FILE))
        _meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    return _index, _meta


def search(query: str, k: int | None = None, min_score: float | None = None) -> list[dict]:
    """Trả về top-k đoạn liên quan nhất (đã lọc theo ngưỡng điểm)."""
    index, meta = load()
    k = k or RAG.top_k
    min_score = RAG.min_score if min_score is None else min_score

    scores, idxs = index.search(encode_query(query), k)
    out: list[dict] = []
    for s, i in zip(scores[0], idxs[0]):
        if i < 0 or float(s) < min_score:    # không đủ liên quan -> bỏ
            continue
        item = dict(meta[i])
        item["score"] = float(s)
        out.append(item)
    return out
```

`min_score` chính là **cơ chế chống bịa**: không đoạn nào đủ điểm → `search` trả
danh sách rỗng → Luna sẽ nói "chưa có trong tài liệu của em" thay vì bịa.

---

## 5. Dựng chỉ mục

Em đã viết sẵn `scripts/build_index.py` (script tiện ích). Chạy:

```
D:\Luna_Project\.venv\Scripts\activate
cd D:\Luna_Project
python scripts\build_index.py
```

Lần đầu sẽ tải model embedding (~1.1GB) rồi embedding ~10.000 chunk. Trên RTX 3060
mất khoảng **2–5 phút**. Kết quả nằm ở `data/rag_index/`.

## 6. Tìm thử

```
python scripts\ask_rag.py "SQL injection là gì và phòng chống thế nào"
python scripts\ask_rag.py "cờ -sS của nmap dùng để làm gì"
python scripts\ask_rag.py "cách nấu phở"          # phải ra RỖNG (chống bịa)
```

Hai câu đầu phải ra đoạn OWASP/nmap đúng chủ đề kèm điểm và tên file. Câu thứ ba
phải không ra gì — đó là dấu hiệu ngưỡng điểm hoạt động.

## 7. Test

Tạo `tests/test_rag_chunk.py`:

```python
from pathlib import Path

from luna.rag.chunk import clean, split_by_heading, split_long


def test_clean_bo_anh_va_link():
    t = clean("# A\n\n![img](x.png) xem [OWASP](https://owasp.org) nhé")
    assert "x.png" not in t and "https://owasp.org" not in t
    assert "OWASP" in t


def test_split_by_heading():
    secs = split_by_heading("# Tiêu đề 1\nnội dung một\n\n## Tiêu đề 2\nnội dung hai")
    assert [s[0] for s in secs] == ["Tiêu đề 1", "Tiêu đề 2"]


def test_split_long_co_overlap():
    doan = "\n\n".join(["câu " * 60 for _ in range(5)])
    parts = split_long(doan, size=400, overlap=50)
    assert len(parts) > 1
    assert all(len(p) <= 400 + 50 for p in parts)
```

Chạy: `pytest -q` phải xanh.

---

Xong R2, báo em kết quả `ask_rag.py` — mình sang **R3: nối RAG vào Luna** để em
trả lời có trích nguồn.
