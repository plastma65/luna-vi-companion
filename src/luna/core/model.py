"""Luna: kiến trúc GPT thu nhỏ (Transformer chỉ-giải-mã), đủ nhỏ để train trên RTX 3060."""

from __future__ import annotations
import torch
import torch.nn as nn
from torch.nn import functional as F


class Head(nn.Module):
    """Một 'đầu' self-attention."""

    def __init__(self, n_embd: int, head_size: int, block_size: int, dropout: float):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        # tril: ma trận tam giác dưới, chặn nhìn về tương lai
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x)  # (B, T, head_size)
        q = self.query(x)
        # điểm tương đồng, chia sqrt(head_size) cho ổn định số học
        wei = q @ k.transpose(-2, -1) * k.shape[-1] ** -0.5  # (B, T, T)
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float("-inf"))
        wei = F.softmax(wei, dim=-1)  # thành xác suất, tổng theo hàng = 1
        wei = self.dropout(wei)
        v = self.value(x)  # (B, T, head_size)
        return wei @ v


class MultiHead(nn.Module):
    """Nhiều Head chạy song song rồi nối lại."""

    def __init__(self, n_head, n_embd, block_size, dropout):
        super().__init__()
        head_size = n_embd // n_head  # chia đều chiều embedding cho các đầu
        self.heads = nn.ModuleList(
            [Head(n_embd, head_size, block_size, dropout) for _ in range(n_head)]
        )
        self.proj = nn.Linear(n_embd, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return self.dropout(self.proj(out))


class FeedFoward(nn.Module):
    """Lớp phi tuyến xử lý riêng từng vị trí sau attention."""

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
        self.ff = FeedFoward(n_embd, dropout)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(
            self.ln1(x)
        )  # residual: cộng đầu vào trở lại giúp mạng sâu vẫn học được (gradient chảy mượt)
        x = x + self.ff(self.ln2(x))
        return x


class Luna(nn.Module):
    def __init__(self, vocab_size, n_embd, n_head, n_layer, block_size, dropout):
        super().__init__()
        self.block_size = block_size
        self.token_emb = nn.Embedding(vocab_size, n_embd)  # ý nghĩa từng token
        self.pos_emb = nn.Embedding(block_size, n_embd)  # vị trí trong câu
        self.blocks = nn.Sequential(
            *[Block(n_embd, n_head, block_size, dropout) for _ in range(n_layer)]
        )
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size)  # đoán token kế

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok = self.token_emb(idx)  # (B, T, n_embd)
        pos = self.pos_emb(torch.arange(T, device=idx.device))
        x = tok + pos  # cộng: token nào + ở đâu
        x = self.blocks(x)
        x = self.ln_f(x)
        logits = self.head(x)  # (B, T, vocab_size)

        loss = None
        if targets is not None:
            B, T, C = logits.shape
            loss = F.cross_entropy(logits.view(B * T, C), targets.view(B * T))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens: int):
        """Sinh chữ: lặp lại đoán token kế rồi nối vào."""
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size :]  # chỉ nhìn block_size token cuối
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :]  # dự đoán ở vị trí cuối
            probs = F.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)  # bốc theo xác suất
            idx = torch.cat((idx, next_id), dim=1)
        return idx
