"""Gửi trạng thái sang orb overlay (nếu đang chạy). An toàn khi overlay tắt.

Trạng thái: 'idle' | 'thinking' | 'speaking'. text = câu hiển thị (caption).
"""

from __future__ import annotations

import requests

OVERLAY_URL = "http://127.0.0.1:5223/state"


def set_state(state: str, text: str = "") -> None:
    try:
        requests.post(OVERLAY_URL, json={"state": state, "text": text}, timeout=0.4)
    except Exception:  # noqa: BLE001  (overlay chưa mở thì bỏ qua)
        pass
