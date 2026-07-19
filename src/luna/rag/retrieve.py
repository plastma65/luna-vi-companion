"""Ghép kết quả tìm kiếm thành 'ngữ cảnh' để đưa cho Luna đọc trước khi trả lời.

Nguyên tắc chống bịa:
  - Có tài liệu liên quan  -> ép Luna CHỈ dựa vào ngữ cảnh, và trích nguồn.
  - Không có tài liệu nào đạt ngưỡng -> KHÔNG chèn gì, Luna trò chuyện bình thường.

Chính ngưỡng min_score trong config đóng vai trò "công tắc": câu tán gẫu ("chào em")
sẽ không lôi tài liệu bảo mật vào, còn câu hỏi kiến thức thì có.
"""

from __future__ import annotations

from luna.config import RAG
from luna.rag.store import search

# Chỉ thị kèm ngữ cảnh. Viết ngắn gọn để đỡ tốn token.
INSTRUCTION = (
    "Dưới đây là các đoạn trích từ tài liệu an ninh mạng trong kho của em "
    "(OWASP, man page nmap, tài liệu Metasploit). Hãy trả lời câu hỏi của anh "
    "CHỈ dựa trên các đoạn này, bằng tiếng Việt, ngắn gọn và dễ hiểu. "
    "Nếu các đoạn không đủ thông tin, nói thẳng là em chưa có tài liệu về phần đó "
    "— tuyệt đối không bịa. Giải thích theo hướng học tập và phòng thủ."
)


def build_context(query: str, k: int | None = None) -> tuple[str, list[dict]]:
    """Trả (khối ngữ cảnh, danh sách nguồn). Không tìm thấy gì -> ('', [])."""
    hits = search(query, k=k or RAG.top_k)
    if not hits:
        return "", []

    parts = []
    for i, h in enumerate(hits, 1):
        parts.append(f"[{i}] ({h['title']})\n{h['text']}")
    block = f"{INSTRUCTION}\n\n===== TÀI LIỆU =====\n" + "\n\n".join(parts) + "\n===== HẾT =====\n"
    return block, hits


def make_prompt(query: str, k: int | None = None) -> tuple[str, list[dict]]:
    """Câu hỏi đã kèm ngữ cảnh, sẵn sàng đưa vào model.

    Nếu không có tài liệu liên quan thì trả lại đúng câu hỏi gốc.
    """
    block, hits = build_context(query, k=k)
    if not block:
        return query, []
    return f"{block}\nCâu hỏi của anh: {query}", hits


def sources_line(hits: list[dict]) -> str:
    """Dòng trích nguồn để IN RA màn hình (không đọc thành tiếng)."""
    if not hits:
        return ""
    seen: list[str] = []
    for h in hits:
        if h["source"] not in seen:
            seen.append(h["source"])
    return "📚 Nguồn: " + " · ".join(seen)
