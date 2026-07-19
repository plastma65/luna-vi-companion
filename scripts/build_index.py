"""Dựng chỉ mục RAG cho Luna từ data/knowledge/ -> data/rag_index/.

Chạy (trong .venv):
    python scripts/build_index.py
    python scripts/build_index.py --dry-run     # chỉ đếm chunk, không embedding
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from luna.config import KNOWLEDGE_DIR, RAG, RAG_INDEX_DIR  # noqa: E402
from luna.rag.chunk import build_chunks  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Dựng chỉ mục RAG cho Luna")
    ap.add_argument("--dry-run", action="store_true", help="chỉ cắt chunk, không embedding")
    args = ap.parse_args()

    if not KNOWLEDGE_DIR.exists():
        print(f"❌ Chưa có {KNOWLEDGE_DIR}. Chạy trước: python scripts/fetch_knowledge.py")
        return 1

    print(f"📚 Đọc tài liệu trong {KNOWLEDGE_DIR} ...")
    t0 = time.time()
    chunks = build_chunks()
    if not chunks:
        print("❌ Không cắt được chunk nào. Kho tài liệu rỗng?")
        return 1

    lens = [len(c.text) for c in chunks]
    print(f"\n✂️  {len(chunks):,} chunk trong {time.time() - t0:.1f}s")
    print(f"   độ dài: min={min(lens)} · trung bình={sum(lens) // len(lens)} · max={max(lens)}")

    def group(src: str) -> str:
        parts = src.split("/")
        return "/".join(parts[:2]) if len(parts) > 1 else parts[0]

    print("   theo nguồn:")
    for name, n in Counter(group(c.source) for c in chunks).most_common():
        print(f"     {name:34s} {n:6,d}")

    if args.dry_run:
        print("\n(--dry-run: dừng ở đây, chưa embedding)")
        return 0

    print(f"\n🧠 Embedding bằng {RAG.embed_model} (lần đầu sẽ tải model)...")
    t1 = time.time()
    from luna.rag.store import build  # import trễ để --dry-run không phải nạp torch

    n = build(chunks)
    print(f"\n✅ Xong {n:,} chunk trong {time.time() - t1:.1f}s")
    print(f"   Chỉ mục: {RAG_INDEX_DIR}")
    print('\nThử ngay:  python scripts\\ask_rag.py "SQL injection là gì"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
