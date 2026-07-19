import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
from luna.config import LUNA, RAW_DIR, CHECKPOINT_DIR
from luna.core.tokenizer import CharTokenizer
from luna.core.model import Luna

cfg = LUNA
device = cfg.device if torch.cuda.is_available() else "cpu"
print("Thiết bị:", device)

# 1) Dữ liệu
text = (RAW_DIR / "corpus.txt").read_text(encoding="utf-8")
tok = CharTokenizer(text)
data = torch.tensor(tok.encode(text), dtype=torch.long)
n = int(0.9 * len(data))
train_data, val_data = data[:n], data[n:]  # 90% train, 10% để kiểm


def get_batch(split):
    d = train_data if split == "train" else val_data
    ix = torch.randint(len(d) - cfg.block_size, (cfg.batch_size,))  # điểm bắt đầu ngẫu nhiên
    x = torch.stack([d[i : i + cfg.block_size] for i in ix])
    y = torch.stack([d[i + 1 : i + 1 + cfg.block_size] for i in ix])  # y = x dịch phải 1
    return x.to(device), y.to(device)


# 2) Model
model = Luna(
    vocab_size=tok.vocab_size,
    n_embd=cfg.n_embd,
    n_head=cfg.n_head,
    n_layer=cfg.n_layer,
    block_size=cfg.block_size,
    dropout=cfg.dropout,
).to(device)
print("Số tham số:", round(sum(p.numel() for p in model.parameters()) / 1e6, 2), "triệu")

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
torch.save(
    {"model": model.state_dict(), "stoi": tok.stoi, "itos": tok.itos}, CHECKPOINT_DIR / "luna.pt"
)
print("Đã lưu checkpoint:", CHECKPOINT_DIR / "luna.pt")
