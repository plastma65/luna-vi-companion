# RAG — Bước R2b: Hiệu chỉnh tìm kiếm (đo thật rồi sửa)

Sau khi dựng chỉ mục, ta đo bằng 3 câu hỏi và phát hiện 2 lỗi. Đây là bước quan
trọng nhất của RAG: **không tin ước lượng, phải đo rồi chỉnh**.

## Kết quả đo (trên kho của anh)

| Câu hỏi | Điểm cao nhất | Nhận xét |
|---|---|---|
| "SQL injection là gì..." | 0.883 | đúng ✅ |
| "cờ -sS của nmap..." | 0.845 | ra nhầm mục `-sO`, `-S` ⚠️ |
| "cách nấu phở" | 0.814 | rác vẫn lọt qua ngưỡng 0.78 ❌ |

**Lỗi 1 — Ngưỡng sai.** Model e5 nén mọi điểm vào dải hẹp 0.78–0.89. Câu hoàn toàn
vô nghĩa vẫn được 0.81. Ngưỡng 0.78 ban đầu quá thấp → đã đổi thành **0.84** trong
`config.py` (ranh giới giữa 0.814 rác và 0.845 đúng).

**Lỗi 2 — Embedding mù với token kỹ thuật.** Đoạn chứa đúng `-sS: TCP SYN scan` có
trong kho nhưng không lọt top-4. Vector giỏi bắt *ý nghĩa chung*, nhưng cờ lệnh
ngắn như `-sS`, `--script`, `msfconsole` thì nó gần như không phân biệt được.

→ Giải pháp: **tìm kiếm lai (hybrid)** = vector lo ý nghĩa + từ khoá lo cờ lệnh.

---

## Sửa 1 — Bỏ file ghi chú khỏi chỉ mục

`SOURCES.md` là file ghi chú của chính mình, không phải kiến thức, nhưng nó lọt vào
top-4 khi hỏi nmap. Trong `src/luna/rag/chunk.py`, sửa hàm `iter_files`:

```python
# Thêm hằng số này ở gần TEXT_EXTS
SKIP_NAMES = {"sources.md", "readme.md", "index.md", "license.md", "contributing.md"}


def iter_files(root: Path | None = None):
    root = root or KNOWLEDGE_DIR
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXTS | PDF_EXTS:
            continue
        if p.name.lower() in SKIP_NAMES:   # file điều hướng/ghi chú -> bỏ
            continue
        yield p
```

## Sửa 2 — Tìm kiếm lai trong `store.py`

Thêm phần này vào đầu `src/luna/rag/store.py` (sau các `import`):

```python
import re

# Từ phổ biến, không mang thông tin -> không dùng để cộng điểm
_STOP = {
    "là", "gì", "của", "dùng", "để", "làm", "và", "cách", "thế", "nào", "cho", "có",
    "các", "những", "một", "khi", "với", "trong", "này", "đó", "ra", "sao", "nhé",
    "giúp", "anh", "em", "luna", "vậy", "được", "bị", "hỏi", "biết", "giải", "thích",
    "the", "what", "how", "and", "for", "with", "does", "use",
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
```

Rồi **thay toàn bộ** hàm `search` cũ bằng bản này:

```python
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
        hay = f"{item['title']} {item['text']}".lower()
        hits = sum(1 for t in terms if t in hay)
        bonus = RAG.keyword_boost * min(hits, RAG.keyword_boost_max)
        item["vector_score"] = float(s)
        item["keyword_hits"] = hits
        item["score"] = float(s) + bonus
        ranked.append(item)

    # 3) Xếp lại theo điểm tổng, lọc ngưỡng, lấy top-k
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return [r for r in ranked if r["score"] >= min_score][:k]
```

### Vì sao cách này hiệu quả

- Câu "nấu phở": từ khoá `nấu`, `phở` **không xuất hiện** trong tài liệu bảo mật →
  không được cộng → giữ nguyên ~0.81 → dưới ngưỡng 0.84 → **bị loại**. ✅
- Câu "-sS của nmap": đoạn chứa đúng `-sS` và `nmap` được cộng `+0.04` → vượt lên
  trên các đoạn nói về `-sO`, `-S`. ✅
- Câu SQL injection: vốn đã đúng, giờ đoạn nào nhắc đúng "sql injection" còn được
  đẩy lên cao hơn. ✅

Điểm mấu chốt: **cộng điểm chứ không lọc theo từ khoá**. Nếu bắt buộc phải khớp từ
khoá thì hỏi tiếng Việt thuần ("lỗ hổng chèn mã") sẽ trượt hết — mất đúng cái hay
của tìm kiếm ngữ nghĩa.

---

## Chạy lại & đo lại

Vì đã đổi `iter_files`, phải dựng lại chỉ mục:

```
python scripts\build_index.py
python scripts\ask_rag.py "cờ -sS của nmap dùng để làm gì"
python scripts\ask_rag.py "cách nấu phở"
python scripts\ask_rag.py "SQL injection là gì và phòng chống thế nào"
```

Kỳ vọng:
- `-sS`: đoạn có `-sS: TCP SYN scan` phải nằm trong top-2.
- "nấu phở": **rỗng**.
- SQL injection: vẫn tốt như cũ.

Nếu "nấu phở" vẫn lọt → nâng `min_score` lên 0.85–0.86 trong `config.py`.
Nếu câu đúng chủ đề lại bị loại hết → hạ xuống 0.83.

## Bài học rút ra

Ngưỡng và cách xếp hạng **không thể đoán trước** — phải dựng chỉ mục, hỏi vài câu
(gồm cả câu vô nghĩa để thử chống bịa), nhìn điểm rồi mới chỉnh. Sau này thêm sách
vào kho, anh nên đo lại y như vậy.
