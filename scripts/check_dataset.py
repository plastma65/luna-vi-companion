"""Kiểm tra file dataset persona (.jsonl) có hợp lệ không.

Chạy:
    python scripts/check_dataset.py data/processed/luna_persona_seed.jsonl

Kiểm: mỗi dòng là JSON hợp lệ, có 'messages', đủ role system/user/assistant,
nội dung không rỗng. Báo lỗi kèm số dòng để dễ sửa.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_ROLES = {"system", "user", "assistant"}


def check(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"Không tìm thấy file: {path}")
        return 1

    n_ok = 0
    n_err = 0
    for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[dòng {lineno}] JSON hỏng: {e}")
            n_err += 1
            continue

        msgs = obj.get("messages")
        if not isinstance(msgs, list) or not msgs:
            print(f"[dòng {lineno}] thiếu 'messages' hoặc rỗng")
            n_err += 1
            continue

        roles = [m.get("role") for m in msgs]
        if "user" not in roles or "assistant" not in roles:
            print(f"[dòng {lineno}] cần có ít nhất 1 user và 1 assistant")
            n_err += 1
            continue
        if any(r not in VALID_ROLES for r in roles):
            print(f"[dòng {lineno}] có role lạ: {roles}")
            n_err += 1
            continue
        if any(not (m.get("content") or "").strip() for m in msgs):
            print(f"[dòng {lineno}] có message nội dung rỗng")
            n_err += 1
            continue

        n_ok += 1

    print(f"\nHợp lệ: {n_ok} mẫu | Lỗi: {n_err}")
    if n_ok < 20:
        print("Gợi ý: nên có >= 20 mẫu seed trước khi nhân bản bằng model thầy.")
    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/luna_persona_seed.jsonl"
    raise SystemExit(check(path))
