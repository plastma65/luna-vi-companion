"""Bộ nhớ dài hạn dạng 'sự kiện' cho Luna.

- facts.json: danh sách những điều Luna nhớ về anh (nạp vào system prompt).
- log.jsonl: nhật ký hội thoại (nền cho tự học sau này).

Lệnh bằng lời:
    "nhớ giúp anh ..."  -> ghi nhớ
    "quên ..."          -> xoá một điều / "quên hết" -> xoá tất cả
    "em nhớ gì về anh"  -> nhắc lại

Lưu ý: chuẩn hoá Unicode NFC để so khớp tiếng Việt chính xác (tránh bẫy tổ hợp/dựng sẵn).
"""

from __future__ import annotations

import json
import time
import unicodedata

from luna.config import DATA_DIR

MEM_DIR = DATA_DIR / "memory"
FACTS_FILE = MEM_DIR / "facts.json"
LOG_FILE = MEM_DIR / "log.jsonl"


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def load_facts() -> list[str]:
    if not FACTS_FILE.exists():
        return []
    try:
        return json.loads(FACTS_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []


def save_facts(facts: list[str]) -> None:
    MEM_DIR.mkdir(parents=True, exist_ok=True)
    FACTS_FILE.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")


def add_fact(text: str) -> bool:
    text = _nfc(text).strip()
    if not text:
        return False
    facts = load_facts()
    if any(text.lower() == f.lower() for f in facts):
        return False
    facts.append(text)
    save_facts(facts)
    return True


def remove_fact(query: str) -> str | None:
    query = _nfc(query).strip().lower()
    if not query:
        return None
    facts = load_facts()
    for f in facts:
        if query in _nfc(f).lower():
            facts.remove(f)
            save_facts(facts)
            return f
    return None


def facts_block() -> str:
    facts = load_facts()
    if not facts:
        return ""
    lines = "\n".join(f"- {f}" for f in facts)
    return f"\n\nNhững điều em đã ghi nhớ về anh (dùng khi phù hợp):\n{lines}"


def log_turn(role: str, text: str) -> None:
    try:
        MEM_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps({"ts": time.time(), "role": role, "text": text}, ensure_ascii=False)
                + "\n"
            )
    except Exception:  # noqa: BLE001
        pass


# ---- từ khoá (đều chuẩn hoá NFC) ----
_RECALL = [
    _nfc(x)
    for x in ["em nhớ gì", "nhớ những gì", "em nhớ được gì", "em biết gì về anh", "em còn nhớ gì"]
]
_REMEMBER = sorted(
    [
        _nfc(x)
        for x in [
            "ghi nhớ giúp",
            "ghi nhớ",
            "nhớ giúp anh",
            "nhớ giúp em",
            "nhớ giúp",
            "nhớ giùm",
            "nhớ dùm",
            "nhớ là",
            "nhớ rằng",
            "hãy nhớ",
            "lưu lại giúp",
            "lưu lại",
        ]
    ],
    key=len,
    reverse=True,
)
_FILLER = [
    _nfc(x)
    for x in ["là ", "rằng ", "giúp ", "cho anh ", "cho em ", "dùm ", "giùm ", "anh ", "em ", ":"]
]
_QUEN = _nfc("quên")
_HAY_QUEN = _nfc("hãy quên")
_XOA1 = _nfc("xoá trí nhớ")
_XOA2 = _nfc("xóa trí nhớ")
_HET = _nfc("hết")
_TATCA = _nfc("tất cả")
_TRINHO = _nfc("trí nhớ")


def _strip_filler(s: str) -> str:
    s = _nfc(s).strip(" :,.-")
    low = s.lower()
    changed = True
    while changed:
        changed = False
        for w in _FILLER:
            if low.startswith(w):
                s = s[len(w) :].strip(" :,.-")
                low = s.lower()
                changed = True
    return s


def memory_command(text: str) -> str | None:
    """Trả câu Luna xác nhận nếu là lệnh bộ nhớ; None nếu không phải."""
    text = _nfc(text)
    t = text.lower().strip()

    if any(k in t for k in _RECALL):
        facts = load_facts()
        if not facts:
            return (
                "Dạ hiện em chưa ghi nhớ điều gì đặc biệt về anh cả. "
                "Anh muốn em nhớ gì thì bảo 'nhớ giúp anh...' nhé 😊"
            )
        return "Dạ em nhớ những điều này về anh ạ: " + "; ".join(facts) + " 🌙"

    if t.startswith(_QUEN) or _HAY_QUEN in t or _XOA1 in t or _XOA2 in t:
        if _HET in t or _TATCA in t or _TRINHO in t:
            save_facts([])
            return "Dạ em đã xoá hết những gì em nhớ rồi ạ."
        i = t.find(_QUEN)
        q = _strip_filler(text[i + len(_QUEN) :])
        removed = remove_fact(q)
        if removed:
            return "Dạ em quên điều đó rồi nhé: " + removed
        return "Dạ em không tìm thấy điều đó trong trí nhớ ạ."

    for trig in _REMEMBER:
        i = t.find(trig)
        if i != -1:
            fact = _strip_filler(text[i + len(trig) :])
            if fact:
                add_fact(fact)
                return f"Dạ em nhớ rồi ạ: {fact} 🌙"
            return None

    return None
