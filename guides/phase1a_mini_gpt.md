# Guide 1a — Tự train Mini-GPT từ số 0

> Mục tiêu: **hiểu** một GPT hoạt động thế nào bằng cách tự tay viết. Kết quả cuối sẽ sinh ra chữ tiếng Việt "lảm nhảm nhưng có vần" — và **đó là thành công**. Đừng kỳ vọng nó trả lời thông minh; việc đó để Giai đoạn 1b.
>
> Cách dùng guide này: **tự gõ code theo từng phần** vào các file được chỉ định. Mình giải thích từng đoạn để bạn hiểu, không chỉ chép. Sau mỗi phần có bước kiểm chứng.

Ước tính: 2–4 tuần nếu bạn mới. Cứ chậm mà chắc.

---

## Bức tranh tổng thể

Một GPT sinh chữ bằng cách **đoán ký tự (token) tiếp theo**. Ta cần 4 mảnh:

1. **Tokenizer** — biến chữ ↔ số.
2. **Model** — mạng Transformer nhận dãy số, đoán số tiếp theo.
3. **Training loop** — cho model xem văn bản thật, chỉnh dần cho đoán đúng hơn.
4. **Generate** — dùng model đã train để sinh chữ mới.

Ta làm đúng thứ tự đó.

---

## Bước 0 — Chuẩn bị dữ liệu

Cần 1 file text tiếng Việt, khoảng **1–5 MB** (truyện, bài viết, phụ đề gộp lại). Lưu vào:

```
data/raw/corpus.txt
```

Yêu cầu: UTF-8, càng "đúng giọng bạn thích" càng tốt (sau này persona nằm ở GĐ1b, giờ chỉ cần tiếng Việt sạch).

> Chưa có data? Tạm dùng vài chương truyện public domain tiếng Việt để chạy thử pipeline.

**Kiểm chứng:**
```powershell
python -c "print(open('data/raw/corpus.txt', encoding='utf-8').read()[:200])"
```
In ra 200 ký tự đầu là ổn.

---

## Bước 1 — Tokenizer mức ký tự

Tạo file **`src/luna/core/tokenizer.py`** và gõ theo:

```python
"""Tokenizer mức ký tự — đơn giản nhất: mỗi ký tự = 1 token.

Đủ để học bản chất. GĐ1b sẽ dùng tokenizer subword của base model.
"""
from __future__ import annotations
from pathlib import Path


class CharTokenizer:
    def __init__(self, text: str):
        # Lấy tập ký tự duy nhất, sắp xếp để ổn định
        chars = sorted(set(text))
        self.vocab_size = len(chars)
        # Hai từ điển tra ngược nhau: ký tự <-> số
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.itos = {i: ch for i, ch in enumerate(chars)}

    def encode(self, s: str) -> list[int]:
        return [self.stoi[c] for c in s]

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos[i] for i in ids)

    @classmethod
    def from_file(cls, path: str | Path) -> "CharTokenizer":
        text = Path(path).read_text(encoding="utf-8")
        return cls(text)
```

**Giải thích:** `stoi` (string→int) và `itos` (int→string) là 2 bảng tra. `encode` đổi chuỗi thành list số; `decode` làm ngược lại. `vocab_size` = số ký tự khác nhau — model cần biết để tạo lớp output đúng cỡ.

**Kiểm chứng (round-trip):** tạo `tests/test_tokenizer.py`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from luna.core.tokenizer import CharTokenizer

def test_roundtrip():
    tok = CharTokenizer("xin chào Luna")
    s = "chào"
    assert tok.decode(tok.encode(s)) == s   # mã hoá rồi giải mã phải ra chuỗi gốc
```
Chạy `pytest -q` → phải xanh.

---

## Bước 2 — Mô hình GPT nhỏ

Tạo **`src/luna/core/model.py`**. Đây là phần "nặng đô" nhất — gõ chậm, đọc comment.

```python
"""Mini-GPT: một Transformer chỉ-giải-mã, đủ nhỏ để train trên RTX 3060."""
from __future__ import annotations
import torch
import torch.nn as nn
from torch.nn import functional as F


class Head(nn.Module):
    """Một 'đầu' self-attention: cho mỗi vị trí nhìn về các vị trí trước đó."""
    def __init__(self, n_embd: int, head_size: int, block_size: int, dropout: float):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        # 'tril' = ma trận tam giác dưới: chặn không cho nhìn về tương lai
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x)
        q = self.query(x)
        # điểm tương đồng giữa các vị trí, chia sqrt để ổn định
        wei = q @ k.transpose(-2, -1) * k.shape[-1] ** -0.5
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float("-inf"))
        wei = F.softmax(wei, dim=-1)
        wei = self.dropout(wei)
        v = self.value(x)
        return wei @ v


class MultiHead(nn.Module):
    """Gộp nhiều Head chạy song song rồi nối lại."""
    def __init__(self, n_head, n_embd, block_size, dropout):
        super().__init__()
        head_size = n_embd // n_head
        self.heads = nn.ModuleList(
            [Head(n_embd, head_size, block_size, dropout) for _ in range(n_head)]
        )
        self.proj = nn.Linear(n_embd, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return self.dropout(self.proj(out))


class FeedForward(nn.Module):
    """Lớp xử lý phi tuyến sau attention."""
    def __init__(self, n_embd, dropout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.ReLU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class Block(nn.Module):
    """1 khối Transformer = attention + feedforward, có residual + layernorm."""
    def __init__(self, n_embd, n_head, block_size, dropout):
        super().__init__()
        self.sa = MultiHead(n_head, n_embd, block_size, dropout)
        self.ff = FeedForward(n_embd, dropout)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(self.ln1(x))   # residual: cộng lại đầu vào
        x = x + self.ff(self.ln2(x))
        return x


class MiniGPT(nn.Module):
    def __init__(self, vocab_size, n_embd, n_head, n_layer, block_size, dropout):
        super().__init__()
        self.block_size = block_size
        self.token_emb = nn.Embedding(vocab_size, n_embd)      # ý nghĩa từng token
        self.pos_emb = nn.Embedding(block_size, n_embd)        # vị trí trong câu
        self.blocks = nn.Sequential(
            *[Block(n_embd, n_head, block_size, dropout) for _ in range(n_layer)]
        )
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size)              # đoán token tiếp theo

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok = self.token_emb(idx)
        pos = self.pos_emb(torch.arange(T, device=idx.device))
        x = tok + pos
        x = self.blocks(x)
        x = self.ln_f(x)
        logits = self.head(x)

        loss = None
        if targets is not None:
            B, T, C = logits.shape
            loss = F.cross_entropy(logits.view(B * T, C), targets.view(B * T))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens: int):
        """Sinh chữ: lặp lại việc đoán token kế rồi nối vào."""
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]      # chỉ nhìn block_size token cuối
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :]                 # lấy dự đoán ở vị trí cuối
            probs = F.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)  # bốc theo xác suất
            idx = torch.cat((idx, next_id), dim=1)
        return idx
```

**Giải thích cốt lõi:**
- `token_emb` + `pos_emb`: model cần biết *token gì* và *ở vị trí nào*.
- `Head`/`MultiHead`: cơ chế **self-attention** — trái tim của Transformer. `tril` đảm bảo đoán token thứ t chỉ dựa vào các token trước đó (không "gian lận" nhìn tương lai).
- `Block` xếp chồng `n_layer` lần → model sâu hơn, hiểu ngữ cảnh tốt hơn.
- `generate` là vòng lặp sinh chữ: đoán → nối → đoán tiếp.

Đừng lo nếu chưa thấm hết. Chạy được rồi quay lại đọc sẽ ngấm.

---

## Bước 3 — Training loop

Tạo **`scripts/train_minigpt.py`**:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
from luna.config import MINI_GPT, RAW_DIR, CHECKPOINT_DIR
from luna.core.tokenizer import CharTokenizer
from luna.core.model import MiniGPT

cfg = MINI_GPT
device = cfg.device if torch.cuda.is_available() else "cpu"
print("Thiết bị:", device)

# 1) Dữ liệu
text = (RAW_DIR / "corpus.txt").read_text(encoding="utf-8")
tok = CharTokenizer(text)
data = torch.tensor(tok.encode(text), dtype=torch.long)
n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]

def get_batch(split):
    d = train_data if split == "train" else val_data
    ix = torch.randint(len(d) - cfg.block_size, (cfg.batch_size,))
    x = torch.stack([d[i:i + cfg.block_size] for i in ix])
    y = torch.stack([d[i + 1:i + 1 + cfg.block_size] for i in ix])
    return x.to(device), y.to(device)

# 2) Model
model = MiniGPT(
    vocab_size=tok.vocab_size, n_embd=cfg.n_embd, n_head=cfg.n_head,
    n_layer=cfg.n_layer, block_size=cfg.block_size, dropout=cfg.dropout,
).to(device)
print("Số tham số:", sum(p.numel() for p in model.parameters()) / 1e6, "triệu")

opt = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate)

# 3) Vòng lặp train
for step in range(cfg.max_steps):
    xb, yb = get_batch("train")
    _, loss = model(xb, yb)
    opt.zero_grad(set_to_none=True)
    loss.backward()
    opt.step()
    if step % cfg.eval_interval == 0:
        print(f"step {step:5d} | loss {loss.item():.4f}")

# 4) Lưu checkpoint
CHECKPOINT_DIR.mkdir(exist_ok=True)
torch.save({"model": model.state_dict(), "stoi": tok.stoi, "itos": tok.itos},
           CHECKPOINT_DIR / "minigpt.pt")
print("Đã lưu checkpoint.")
```

**Giải thích:** `get_batch` cắt ngẫu nhiên các đoạn dài `block_size`; `y` là `x` dịch phải 1 ký tự (đáp án "token kế"). Vòng lặp: đoán → tính loss → `backward()` tính gradient → `opt.step()` chỉnh tham số. Loss **phải giảm dần**.

**Chạy:**
```powershell
python scripts/train_minigpt.py
```
Trên RTX 3060, cấu hình mặc định vài phút là thấy loss giảm rõ.

---

## Bước 4 — Sinh chữ

Tạo **`scripts/chat_minigpt.py`**:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
from luna.config import MINI_GPT, CHECKPOINT_DIR
from luna.core.model import MiniGPT

cfg = MINI_GPT
device = cfg.device if torch.cuda.is_available() else "cpu"
ckpt = torch.load(CHECKPOINT_DIR / "minigpt.pt", map_location=device)
itos = ckpt["itos"]

model = MiniGPT(
    vocab_size=len(itos), n_embd=cfg.n_embd, n_head=cfg.n_head,
    n_layer=cfg.n_layer, block_size=cfg.block_size, dropout=cfg.dropout,
).to(device)
model.load_state_dict(ckpt["model"])
model.eval()

start = torch.zeros((1, 1), dtype=torch.long, device=device)
out = model.generate(start, max_new_tokens=500)[0].tolist()
print("".join(itos[i] for i in out))
```

Chạy `python scripts/chat_minigpt.py` → Luna phiên bản mini nhả ra 500 ký tự. Sẽ ngô nghê — **đúng như dự kiến**. Bạn vừa tự train một GPT từ số 0. 🎉

---

## Bước 5 — Smoke test cho pipeline (bắt buộc)

Tạo **`tests/test_mini_gpt.py`** — train 2 step trên data tí hon, chắc không vỡ:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
torch = pytest.importorskip("torch")  # bỏ qua test nếu chưa cài torch

from luna.core.tokenizer import CharTokenizer
from luna.core.model import MiniGPT


def test_minigpt_trains_two_steps():
    text = "xin chào luna " * 50
    tok = CharTokenizer(text)
    data = torch.tensor(tok.encode(text), dtype=torch.long)

    block = 8
    model = MiniGPT(vocab_size=tok.vocab_size, n_embd=16, n_head=2,
                    n_layer=2, block_size=block, dropout=0.0)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

    x = data[:block].unsqueeze(0)
    y = data[1:block + 1].unsqueeze(0)
    for _ in range(2):
        _, loss = model(x, y)
        opt.zero_grad(); loss.backward(); opt.step()

    assert torch.isfinite(loss), "Loss phải hữu hạn, không NaN/inf"

    out = model.generate(x, max_new_tokens=5)
    assert out.shape[1] == block + 5    # sinh đúng số token
```

Chạy `pytest -q`. Xanh = pipeline lành. Từ giờ mỗi lần sửa model, chạy lại test này trước.

---

## Xong 1a thì làm gì?
- Thử tăng `n_layer`, `n_embd`, `max_steps` xem chữ mượt hơn không (chú ý VRAM).
- Đọc lại `model.py` cho đến khi giải thích được self-attention bằng lời của bạn.
- Khi thoải mái, sang **`guides/phase1b_finetune.md`** (mình sẽ viết cùng bạn khi tới bước đó) để dựng Luna nói chuyện thật bằng fine-tune QLoRA.

Bí chỗ nào cứ hỏi mình theo từng bước — đừng gộp cả 5 bước một lúc.
