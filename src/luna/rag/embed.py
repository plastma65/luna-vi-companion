"""Embedding: đổi chữ thành vector bằng model đa ngữ (e5)."""

from __future__ import annotations

import numpy as np

from luna.config import RAG

_model = None


def get_model():
    """Nạp model 1 lần (lazy) rồi dùng lại."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        print(f"Đang nạp embedding model: {RAG.embed_model} ...")
        _model = SentenceTransformer(RAG.embed_model)
    return _model


def _encode(texts: list[str], prefix: str) -> np.ndarray:
    model = get_model()
    vecs = model.encode(
        [prefix + t for t in texts],
        batch_size=RAG.embed_batch,
        normalize_embeddings=True,  # chuẩn hoá -> dot product = cosine
        show_progress_bar=len(texts) > 200,
    )
    return np.asarray(vecs, dtype="float32")


def encode_passages(texts: list[str]) -> np.ndarray:
    """Vector cho TÀI LIỆU (e5 yêu cầu tiền tố 'passage: ')."""
    return _encode(texts, "passage: ")


def encode_query(query: str) -> np.ndarray:
    """Vector cho CÂU HỎI (tiền tố 'query: ')."""
    return _encode([query], "query: ")
