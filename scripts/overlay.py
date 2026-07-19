"""Orb overlay kiểu Jarvis/Gemini cho Luna.

- Cửa sổ KHÔNG khung, NỀN TRONG SUỐT (thấy xuyên xuống desktop), LUÔN NỔI trên cùng.
- Orb (quả cầu phát sáng) đổi hiệu ứng theo trạng thái:
    idle     : "thở" nhẹ
    thinking : vòng sáng xoay (đang suy nghĩ)
    speaking : phồng–xẹp theo nhịp (đang nói)
- Pill chữ (caption) hiện câu Luna đang nói, kiểu Gemini.
- Nhận lệnh trạng thái qua HTTP local: POST http://127.0.0.1:5223/state {"state","text"}

Cách dùng:
    pip install PySide6
    python scripts/overlay.py            # chạy kèm demo tự đổi trạng thái
    python scripts/overlay.py --nodemo   # đứng yên chờ Luna điều khiển

Kéo chuột để di chuyển orb. Chuột phải hoặc Esc để thoát.
"""

from __future__ import annotations

import json
import math
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from PySide6.QtCore import Qt, QTimer, QObject, Signal, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QPen, QFont, QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget

# Khi chạy bằng pythonw (không console): stdout=None -> ghi log ra file, tránh print lỗi
if sys.stdout is None or sys.stderr is None:
    from pathlib import Path as _P

    _ld = _P(__file__).resolve().parents[1] / "logs"
    _ld.mkdir(exist_ok=True)
    _lf = open(_ld / "overlay.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _lf
    sys.stderr = sys.stderr or _lf

PORT = 5223
W, H = 560, 260  # kích thước canvas (đủ chỗ cho orb + caption)
ORB_CX, ORB_CY = W // 2, 84
STATES = {"idle", "thinking", "speaking"}


class Bridge(QObject):
    """Cầu nối an toàn giữa luồng HTTP và luồng giao diện."""

    stateChanged = Signal(str, str)


class Orb(QWidget):
    def __init__(self, demo: bool):
        super().__init__()
        self.state = "idle"
        self.text = ""
        self.phase = 0.0
        self.demo = demo
        self._drag = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(W, H)
        self._move_to_corner()

        # animation ~33fps
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

        if demo:
            self._demo_states = ["idle", "thinking", "speaking"]
            self._demo_i = 0
            self.demo_timer = QTimer(self)
            self.demo_timer.timeout.connect(self._demo_step)
            self.demo_timer.start(2600)
            self.apply_state("idle", "Luna đang chờ anh...")

    def _move_to_corner(self):
        scr = QGuiApplication.primaryScreen().availableGeometry()
        self.move(scr.right() - W - 20, scr.bottom() - H - 20)

    def _demo_step(self):
        self._demo_i = (self._demo_i + 1) % len(self._demo_states)
        s = self._demo_states[self._demo_i]
        txt = {
            "idle": "Luna đang chờ anh...",
            "thinking": "Để em suy nghĩ chút nha...",
            "speaking": "Dạ em nghe anh đây, em giúp được gì cho anh ạ?",
        }[s]
        self.apply_state(s, txt)

    def apply_state(self, state: str, text: str = ""):
        # gọi từ HTTP -> tắt demo để nghe Luna thật
        if state not in STATES:
            state = "idle"
        if not self.demo or state != "idle":
            self.demo = False
        self.state = state
        if text:
            self.text = text
        elif state == "idle":
            self.text = ""
        self.update()

    def _tick(self):
        self.phase += 0.12
        self.update()

    # ---------- vẽ ----------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        t = self.phase
        # màu chủ đạo: xanh tím kiểu mặt trăng
        core = QColor(150, 180, 255)
        if self.state == "speaking":
            core = QColor(170, 200, 255)

        # biên độ phồng theo trạng thái
        if self.state == "idle":
            r = 40 + 3 * math.sin(t * 0.9)
        elif self.state == "thinking":
            r = 42 + 2 * math.sin(t * 1.6)
        else:  # speaking
            r = 46 + 9 * abs(math.sin(t * 2.4)) + 3 * math.sin(t * 5.1)

        cx, cy = ORB_CX, ORB_CY

        # quầng sáng ngoài
        glow = QRadialGradient(QPointF(cx, cy), r * 2.4)
        g = QColor(core)
        g.setAlpha(70)
        glow.setColorAt(0.0, g)
        g2 = QColor(core)
        g2.setAlpha(0)
        glow.setColorAt(1.0, g2)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QPointF(cx, cy), r * 2.4, r * 2.4)

        # lõi orb
        grad = QRadialGradient(QPointF(cx - r * 0.25, cy - r * 0.25), r * 1.4)
        c0 = QColor(235, 242, 255)
        grad.setColorAt(0.0, c0)
        grad.setColorAt(0.5, core)
        cout = QColor(90, 110, 200)
        grad.setColorAt(1.0, cout)
        p.setBrush(grad)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # thinking: vòng cung xoay quanh orb
        if self.state == "thinking":
            pen = QPen(QColor(180, 205, 255, 220), 3)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            rr = r + 14
            rect = QRectF(cx - rr, cy - rr, 2 * rr, 2 * rr)
            a = int((t * 120) % 360)
            p.drawArc(rect, a * 16, 90 * 16)
            p.drawArc(rect, (a + 180) * 16, 90 * 16)

        # speaking: các vòng lan toả
        if self.state == "speaking":
            for k in range(3):
                rr = r + 10 + k * 12 + 6 * math.sin(t * 2.4 - k)
                al = max(0, 120 - k * 40)
                p.setPen(QPen(QColor(170, 200, 255, al), 2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(cx, cy), rr, rr)

        # caption pill
        if self.text:
            self._draw_caption(p)

    def _draw_caption(self, p: QPainter):
        font = QFont("Segoe UI", 11)
        p.setFont(font)
        margin = 24
        max_w = W - 2 * margin
        metrics = p.fontMetrics()
        text = metrics.elidedText(self.text, Qt.ElideRight, max_w * 2)
        # bọc 2 dòng đơn giản
        rect = QRectF(margin, ORB_CY + 60, max_w, 90)
        # nền pill
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(20, 22, 30, 210))
        p.drawRoundedRect(rect, 18, 18)
        # chữ
        p.setPen(QColor(235, 238, 245))
        p.drawText(rect.adjusted(16, 8, -16, -8), Qt.AlignLeft | Qt.TextWordWrap, text)

    # ---------- tương tác ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            QApplication.quit()
        elif e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, _):
        self._drag = None

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            QApplication.quit()


def start_http(bridge: Bridge):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(n) or b"{}")
            except Exception:  # noqa: BLE001
                data = {}
            bridge.stateChanged.emit(str(data.get("state", "idle")), str(data.get("text", "")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *a):
            pass

    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


def main():
    demo = "--nodemo" not in sys.argv
    app = QApplication(sys.argv)
    bridge = Bridge()
    orb = Orb(demo)
    bridge.stateChanged.connect(orb.apply_state)  # queued (an toàn liên luồng)
    threading.Thread(target=start_http, args=(bridge,), daemon=True).start()
    orb.show()
    print(f"🌙 Orb overlay đang chạy. Điều khiển: POST http://127.0.0.1:{PORT}/state")
    print("   Kéo chuột để di chuyển, chuột phải hoặc Esc để thoát.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
