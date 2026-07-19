"""Kho vector FAISS: dựng chỉ mục, lưu ra file, nạp lại, tìm kiếm."""

from __future__ import annotations

import json
import re

from luna.config import RAG, RAG_INDEX_DIR
from luna.rag.embed import encode_passages, encode_query

INDEX_FILE = RAG_INDEX_DIR / "luna.faiss"
META_FILE = RAG_INDEX_DIR / "luna_meta.json"

# Từ phổ biến, không mang thông tin -> không dùng để cộng điểm
_STOP = {
    "là",
    "gì",
    "của",
    "dùng",
    "để",
    "làm",
    "và",
    "cách",
    "thế",
    "nào",
    "cho",
    "có",
    "các",
    "những",
    "một",
    "khi",
    "với",
    "trong",
    "này",
    "đó",
    "ra",
    "sao",
    "nhé",
    "giúp",
    "anh",
    "em",
    "luna",
    "vậy",
    "được",
    "bị",
    "hỏi",
    "biết",
    "giải",
    "thích",
    "the",
    "what",
    "how",
    "and",
    "for",
    "with",
    "does",
    "use",
}


def _key_terms(query: str) -> list[str]:
    """Rút từ khoá kỹ thuật: cờ lệnh (-sS, --script) và từ có nghĩa."""
    raw = re.findall(r"-{1,2}[a-z0-9]{1,15}|[\wÀ-ỹ][\wÀ-ỹ.]{2,}", query.lower())
    out: list[str] = []
    for t in raw:
        t = t.strip(".")
        if len(t) < 2 or t in _STOP or t in out:
            continue
        out.append(t)
    return out


def _count_terms(terms: list[str], haystack: str) -> int:
    """Đếm từ khoá xuất hiện, khớp theo RANH GIỚI TỪ.

    Quan trọng với cờ lệnh: '-sS' không được khớp nhầm bên trong '--ssl'.
    """
    n = 0
    for t in terms:
        # cờ lệnh: hai bên không được là chữ/số/gạch ngang
        pat = (
            rf"(?<![\w-]){re.escape(t)}(?![\w-])"
            if t.startswith("-")
            else rf"(?<!\w){re.escape(t)}(?!\w)"
        )
        if re.search(pat, haystack):
            n += 1
    return n


_index = None
_meta: list[dict] | None = None


def build(chunks: list) -> int:
    """Embedding toàn bộ chunk rồi lưu chỉ mục + metadata ra đĩa."""
    import faiss

    # Ghép tiêu đề vào nội dung để vector giàu ngữ cảnh hơn
    texts = [f"{c.title}\n{c.text}" for c in chunks]
    vecs = encode_passages(texts)

    index = faiss.IndexFlatIP(vecs.shape[1])  # inner product (vector đã chuẩn hoá) = cosine
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
            raise FileNotFoundError("Chưa có chỉ mục. Chạy trước: python scripts\\build_index.py")
        _index = faiss.read_index(str(INDEX_FILE))
        _meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    return _index, _meta


def search(query: str, k: int | None = None, min_score: float | None = None) -> list[dict]:
    """Tìm lai: vector (ý nghĩa) + cộng điểm khi khớp từ khoá kỹ thuật."""
    index, meta = load()
    k = k or RAG.top_k
    min_score = RAG.min_score if min_score is None else min_score

    # 1) Lấy DƯ bằng vector (pool) để còn chỗ xếp lại
    pool = max(RAG.pool_size, k)
    scores, idxs = index.search(encode_query(query), pool)

    # 2) Cộng điểm cho chunk chứa đúng từ khoá kỹ thuật của câu hỏi
    terms = _key_terms(query)
    ranked: list[dict] = []
    for s, i in zip(scores[0], idxs[0]):
        if i < 0:
            continue
        item = dict(meta[i])
        # Khớp ở tiêu đề nặng hơn khớp trong thân bài
        t_hits = _count_terms(terms, item["title"].lower())
        b_hits = _count_terms(terms, item["text"].lower())
        bonus = RAG.title_boost * min(t_hits, RAG.keyword_boost_max) + RAG.keyword_boost * min(
            b_hits, RAG.keyword_boost_max
        )
        item["vector_score"] = float(s)
        item["title_hits"] = t_hits
        item["keyword_hits"] = b_hits
        item["score"] = float(s) + bonus
        ranked.append(item)

    # 3) Xếp lại theo điểm tổng, lọc ngưỡng, lấy top-k
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return [r for r in ranked if r["score"] >= min_score][:k]
