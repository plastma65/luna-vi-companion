import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
from luna.config import LUNA, CHECKPOINT_DIR
from luna.core.model import Luna

cfg = LUNA
device = cfg.device if torch.cuda.is_available() else "cpu"

# Nạp checkpoint đã train
ckpt = torch.load(CHECKPOINT_DIR / "luna.pt", map_location=device, weights_only=False)
itos = ckpt["itos"]

model = Luna(
    vocab_size=len(itos),
    n_embd=cfg.n_embd,
    n_head=cfg.n_head,
    n_layer=cfg.n_layer,
    block_size=cfg.block_size,
    dropout=cfg.dropout,
).to(device)
model.load_state_dict(ckpt["model"])
model.eval()  # tắt dropout khi dùng

# Bắt đầu từ 1 token rỗng rồi sinh 500 ký tự
start = torch.zeros((1, 1), dtype=torch.long, device=device)
out = model.generate(start, max_new_tokens=500)[0].tolist()
print("".join(itos[i] for i in out))
