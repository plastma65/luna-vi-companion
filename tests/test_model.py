import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

torch = pytest.importorskip("torch")
from luna.core.model import Block


def test_block_giu_dung_shape():
    B, T, C = 2, 8, 32  # batch=2, độ dài=8, n_embd=32
    x = torch.randn(B, T, C)  # tensor ngẫu nhiên giả làm đầu vào
    block = Block(n_embd=C, n_head=4, block_size=T, dropout=0.0)
    y = block(x)
    assert y.shape == x.shape  # ra vào phải cùng hình dạng (B, T, C)
    assert torch.isfinite(y).all()  # không có NaN/inf
