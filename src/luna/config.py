"""Cấu hình tập trung cho Luna.

Mọi hằng số/đường dẫn để ở đây, KHÔNG rải rác trong code.
Sửa 1 chỗ, cả dự án đổi theo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# --- Đường dẫn gốc dự án ---
ROOT = Path(__file__).resolve().parents[2]  # .../Luna_Project
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHECKPOINT_DIR = ROOT / "checkpoints"


@dataclass
class LunaConfig:
    """Siêu tham số cho Luna (Giai đoạn 1a).

    Giá trị mặc định vừa cho RTX 3060 12GB. Bạn sẽ chỉnh khi làm guide 1a.
    """

    # Kích thước model
    block_size: int = 128  # độ dài ngữ cảnh (số token nhìn về sau)
    n_embd: int = 256  # số chiều embedding
    n_head: int = 4  # số "đầu" attention
    n_layer: int = 4  # số block Transformer
    dropout: float = 0.1

    # Huấn luyện
    batch_size: int = 32
    learning_rate: float = 3e-4
    max_steps: int = 5000
    eval_interval: int = 250
    device: str = "cuda"  # đổi "cpu" nếu chưa có GPU


# Cấu hình mặc định dùng chung
LUNA = LunaConfig()


@dataclass
class LunaSFTConfig:
    """Cấu hình fine-tune QLoRA (Giai đoạn 1b).

    Mặc định an toàn cho RTX 3060 12GB.
    """

    base_model: str = "Qwen/Qwen3-4B-Instruct-2507"  # model nền open-weights
    max_len: int = 1024  # độ dài tối đa mỗi mẫu (token)
    # LoRA
    r: int = 16  # "độ dày" adapter
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    # Huấn luyện
    batch_size: int = 1
    grad_accum: int = 4  # gộp 4 mẫu mới cập nhật 1 lần (đỡ VRAM)
    lr: float = 2e-4
    epochs: int = 6  # data nhỏ nên cần nhiều epoch để "ngấm"


SFT = LunaSFTConfig()
ADAPTER_DIR = CHECKPOINT_DIR / "luna_lora"  # nơi lưu adapter sau train


# --- RAG (Giai đoạn 3: Luna tra cứu tài liệu) ---
KNOWLEDGE_DIR = DATA_DIR / "knowledge"  # tài liệu nguồn (OWASP, manpage, sách)
RAG_INDEX_DIR = DATA_DIR / "rag_index"  # chỉ mục FAISS + metadata


@dataclass
class LunaRAGConfig:
    """Cấu hình RAG. Chỉnh ở đây, không rải hằng số trong code."""

    # Embedding: bản đa ngữ để hỏi tiếng Việt vẫn khớp tài liệu tiếng Anh.
    # Máy yếu/ít VRAM -> đổi sang "intfloat/multilingual-e5-small".
    embed_model: str = "intfloat/multilingual-e5-base"
    embed_batch: int = 64

    # Cắt chunk (đơn vị: ký tự)
    chunk_size: int = 800  # ~1 đoạn vừa đủ ý
    chunk_overlap: int = 120  # gối đầu để không cắt cụt giữa ý
    min_chunk: int = 80  # ngắn hơn thì bỏ (rác, dòng tiêu đề trơ trọi)

    # Tìm kiếm
    top_k: int = 4  # số đoạn đưa cho Luna đọc
    # Ngưỡng liên quan. LƯU Ý: e5 nén điểm vào dải hẹp — đo thực tế trên kho này:
    #   câu đúng chủ đề ~0.84-0.89 · câu vô nghĩa ("nấu phở") ~0.81
    # nên 0.84 là ranh giới hợp lý. Chỉnh lại nếu đổi model embedding.
    min_score: float = 0.84
    # Lấy dư rồi mới xếp lại (rerank) — cần cho phần cộng điểm từ khoá
    pool_size: int = 40
    # Cộng điểm khi chunk chứa đúng từ khoá kỹ thuật của câu hỏi (vd '-sS', 'nmap').
    # Khớp ở TIÊU ĐỀ nặng hơn hẳn khớp trong thân bài: chunk có '-sS' là tiêu đề
    # chính đáng giá hơn nhiều chunk chỉ nhắc thoáng qua '-sS' giữa bài.
    title_boost: float = 0.05
    keyword_boost: float = 0.01  # khớp trong thân bài
    keyword_boost_max: int = 3  # cộng tối đa 3 lần mỗi loại


RAG = LunaRAGConfig()
