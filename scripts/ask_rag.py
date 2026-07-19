"""Tra cứu thử chỉ mục RAG (chưa qua Luna) — để kiểm chất lượng tìm kiếm.

Chạy:
    python scripts/ask_rag.py "SQL injection là gì"
    python scripts/ask_rag.py "cờ -sS của nmap" -k 6
    python scripts/ask_rag.py            # chế độ hỏi liên tục
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from luna.config import RAG  # noqa: E402
from luna.rag.store import search  # noqa: E402


def show(query: str, k: int, min_score: float) -> None:
    hits = search(query, k=k, min_score=min_score)
    print(f"\n❓ {query}")
    if not hits:
        print(
            f"   (không có đoạn nào đạt ngưỡng {min_score} — Luna sẽ nói 'chưa có trong tài liệu')"
        )
        return
    for i, h in enumerate(hits, 1):
        body = h["text"].replace("\n", " ")
        if len(body) > 300:
            body = body[:300] + "..."
        detail = ""
        if "vector_score" in h:  # bản tìm lai: điểm gốc + từ khoá khớp ở tiêu đề/thân bài
            detail = (
                f" (vector {h['vector_score']:.3f}"
                f" + tiêu đề {h.get('title_hits', 0)}"
                f" + thân bài {h['keyword_hits']})"
            )
        print(f"\n  [{i}] điểm {h['score']:.3f}{detail} — {h['title']}")
        print(f"      nguồn: {h['source']}")
        print(f"      {body}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Tra cứu thử chỉ mục RAG của Luna")
    ap.add_argument("query", nargs="*", help="câu hỏi (bỏ trống = hỏi liên tục)")
    ap.add_argument(
        "-k", type=int, default=RAG.top_k, help=f"số đoạn lấy về (mặc định {RAG.top_k})"
    )
    ap.add_argument(
        "--min-score",
        type=float,
        default=RAG.min_score,
        help=f"ngưỡng liên quan (mặc định {RAG.min_score})",
    )
    args = ap.parse_args()

    if args.query:
        show(" ".join(args.query), args.k, args.min_score)
        return 0

    print("Chế độ hỏi liên tục. Gõ 'thoát' để dừng.")
    while True:
        try:
            q = input("\nHỏi: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in {"thoát", "thoat", "quit", "exit"}:
            break
        show(q, args.k, args.min_score)
    return 0


if __name__ == "__main__":
    sys.exit(main())
