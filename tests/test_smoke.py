"""Smoke test tối giản — chạy được ngay cả khi CHƯA cài torch.

Mục đích: cho bạn thấy pytest hoạt động thế nào và cấu trúc dự án import được.
Chạy: pytest -q
"""

import sys
from pathlib import Path

# Cho phép import package luna từ thư mục src/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_import_luna():
    import luna

    assert luna.__version__


def test_config_paths_exist():
    from luna import config

    # Thư mục data phải tồn tại (đã tạo sẵn trong scaffold)
    assert config.DATA_DIR.exists()
    assert config.RAW_DIR.exists()


def test_luna_config_defaults():
    from luna.config import LUNA

    # Vài kiểm tra sanity cho siêu tham số
    assert LUNA.n_embd % LUNA.n_head == 0, "n_embd phải chia hết cho n_head"
    assert LUNA.block_size > 0
    assert 0.0 <= LUNA.dropout < 1.0
