import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

torch = pytest.importorskip("torch")
from luna.core.tokenizer import CharTokenizer
from luna.core.model import Luna


def test_luna_train_2_step():
    text = "xin chào luna " * 50
    tok = CharTokenizer(text)
    data = torch.tensor(tok.encode(text), dtype=torch.long)

    block = 8
    model = Luna(
        vocab_size=tok.vocab_size, n_embd=16, n_head=2, n_layer=2, block_size=block, dropout=0.0
    )
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

    x = data[:block].unsqueeze(0)  # thêm chiều batch -> (1, block)
    y = data[1 : block + 1].unsqueeze(0)  # đáp án = dịch phải 1 ký tự
    first = None
    for _ in range(30):
        _, loss = model(x, y)
        if first is None:
            first = loss.item()
        opt.zero_grad()
        loss.backward()
        opt.step()

    assert torch.isfinite(loss), "Loss phải hữu hạn"
    assert loss.item() < first, "Loss phải GIẢM sau khi train"  # bằng chứng học được

    out = model.generate(x, max_new_tokens=5)
    assert out.shape[1] == block + 5  # sinh đúng số token
