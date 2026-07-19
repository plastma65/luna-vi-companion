"""Tokenizer mức kí tự - mỗi kí tự = 1 token. Đơn giản nhất để học bản chất."""

from __future__ import annotations
from pathlib import Path


class CharTokenizer:
    def __init__(self, text: str):
        chars = sorted(set(text))  # tập kí tự duy nhất
        self.vocab_size = len(chars)
        self.stoi = {ch: i for i, ch in enumerate(chars)}  # kí tự => số
        self.itos = {i: ch for i, ch in enumerate(chars)}  # số => kí tự
        self.unk_id = len(chars)
        self.itos[self.unk_id] = "�"  # ký hiệu lạ (unk) để tránh crash khi gặp kí tự lạ
        self.vocab_size = len(chars) + 1  # tăng vocab_size lên 1 vì có thêm ký hiệu lạ (unk)

    """Chữ sẽ được đổi sang số cho model học"""

    def encode(self, s: str) -> list[int]:
        return [self.stoi.get(c, self.unk_id) for c in s]

    """Model học xong sẽ đổi số về chữ để đọc được"""

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos[i] for i in ids)

    @classmethod
    def from_file(cls, path: str | Path) -> "CharTokenizer":
        return cls(Path(path).read_text(encoding="utf-8"))
