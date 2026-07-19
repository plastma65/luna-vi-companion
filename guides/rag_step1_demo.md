# RAG — Bước R1: Demo tí hon (hiểu embedding + FAISS)

Mục tiêu: chạy một ví dụ ~6 câu để anh **thấy tận mắt** semantic search hoạt động
(hỏi tiếng Việt, khớp đúng câu dù không trùng từ khóa). Hiểu xong bước này, các
bước sau chỉ là "phóng to" nó lên tài liệu thật.

## 1. Cài thư viện (trong `.venv` chính)

```
D:\Luna_Project\.venv\Scripts\activate
pip install sentence-transformers faiss-cpu pypdf
```

- `sentence-transformers`: nạp embedding model, đổi câu → vector.
- `faiss-cpu`: kho vector + tìm nhanh (chạy bằng file, không cần server).
- `pypdf`: để đọc PDF ở bước sau.

`sentence-transformers` dùng lại `torch`/`transformers` đã có nên không nặng thêm nhiều.

## 2. Tạo file demo

Tạo `scripts/rag_demo.py` và gõ:

```python
"""Demo RAG tí hon: embedding 6 câu + tìm kiếm theo ý nghĩa bằng FAISS."""
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Model đa ngữ bản 'small' cho nhẹ (demo). Lần đầu chạy sẽ tự tải (~120MB).
model = SentenceTransformer("intfloat/multilingual-e5-small")

docs = [
    "Nmap là công cụ quét cổng và dò dịch vụ đang chạy trên mạng.",
    "SQL injection là lỗ hổng chèn mã SQL qua ô nhập liệu để đọc trộm cơ sở dữ liệu.",
    "XSS cho phép kẻ tấn công chèn mã JavaScript vào trang web nạn nhân.",
    "Metasploit là framework khai thác lỗ hổng dùng trong kiểm thử xâm nhập.",
    "Burp Suite là proxy chặn bắt và chỉnh sửa request HTTP giữa trình duyệt và server.",
    "Mèo là loài động vật có vú nhỏ, thường được nuôi trong nhà.",
]

# LƯU Ý: model e5 cần tiền tố — 'passage: ' cho tài liệu, 'query: ' cho câu hỏi.
emb = model.encode(["passage: " + d for d in docs], normalize_embeddings=True)
emb = np.asarray(emb, dtype="float32")

# normalize rồi dùng Inner Product = cosine similarity (đo độ gần nghĩa).
index = faiss.IndexFlatIP(emb.shape[1])
index.add(emb)


def hoi(q: str, k: int = 2) -> None:
    qv = model.encode(["query: " + q], normalize_embeddings=True)
    qv = np.asarray(qv, dtype="float32")
    diem, vitri = index.search(qv, k)      # trả về điểm + vị trí k câu gần nhất
    print(f"\nHỏi: {q}")
    for d, i in zip(diem[0], vitri[0]):
        print(f"  [{d:.3f}] {docs[i]}")


if __name__ == "__main__":
    hoi("công cụ nào để quét cổng mạng?")
    hoi("lỗ hổng chèn mã vào cơ sở dữ liệu là gì?")
    hoi("phần mềm chặn bắt request web?")
```

## 3. Chạy

```
cd D:\Luna_Project
python scripts\rag_demo.py
```

Kết quả mong đợi (điểm càng cao càng liên quan):

```
Hỏi: công cụ nào để quét cổng mạng?
  [0.90] Nmap là công cụ quét cổng và dò dịch vụ đang chạy trên mạng.
  [0.83] Metasploit là framework khai thác lỗ hổng ...

Hỏi: lỗ hổng chèn mã vào cơ sở dữ liệu là gì?
  [0.90] SQL injection là lỗ hổng chèn mã SQL qua ô nhập liệu ...
  ...

Hỏi: phần mềm chặn bắt request web?
  [0.89] Burp Suite là proxy chặn bắt và chỉnh sửa request HTTP ...
  ...
```

## 4. Điều cần rút ra

- Anh hỏi **tiếng Việt, dùng từ khác** với tài liệu ("chèn mã vào cơ sở dữ liệu"
  vs "SQL injection") mà vẫn khớp đúng → đó là **semantic search**, sức mạnh của RAG.
- Câu "con mèo" luôn điểm thấp khi hỏi về bảo mật → sau này ta đặt **ngưỡng điểm**
  để Luna biết "không liên quan thì nói không biết", tránh bịa.
- `normalize_embeddings=True` + `IndexFlatIP` = đo **cosine**. Nhớ tiền tố
  `query:` / `passage:` của e5, thiếu là kết quả tệ hẳn.

## 5. Xong bước này báo em

Dán output cho em. Ổn thì sang **R2**: viết `src/luna/rag/` (chunk.py, embed.py,
store.py) và `scripts/build_index.py` để dựng chỉ mục từ tài liệu thật trong
`data/knowledge/`, thay vì 6 câu cứng như demo.
