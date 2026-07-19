# RAG cho Luna — Thiết kế & Lộ trình

Mục tiêu: cho Luna trả lời kiến thức an ninh mạng **dựa trên tài liệu thật, có
nguồn**, thay vì bịa — mà **không train lại model**, **không gọi API ngoài**,
chạy hết offline trên máy anh.

## 1. RAG hoạt động thế nào (1 phút)

```
Câu hỏi của anh
   │  (1) embedding câu hỏi -> vector
   ▼
[Vector store]  --(2) tìm k đoạn gần nghĩa nhất-->  vài "chunk" tài liệu
   │
   ▼
(3) Ghép "Ngữ cảnh = các chunk" + câu hỏi  ->  đưa cho Luna (Qwen)
   │
   ▼
(4) Luna trả lời DỰA TRÊN ngữ cảnh + trích nguồn
```

Không đụng tới trọng số Luna. Muốn Luna "biết" thêm tài liệu mới → chỉ cần thêm
vào kho và dựng lại chỉ mục. Đây là điểm mạnh so với fine-tune.

## 2. Chọn công nghệ (ưu tiên nhẹ, offline, ít phụ thuộc)

| Thành phần | Chọn | Lý do |
|---|---|---|
| Embedding model | `intfloat/multilingual-e5-base` | Đa ngữ: hỏi tiếng Việt vẫn khớp tài liệu tiếng Anh. ~1.1GB, chạy GPU nhẹ. (Máy yếu → `-small`.) |
| Vector store | **FAISS** (`faiss-cpu`) | Lưu ra file, **không cần server** (đúng hướng dự án). Nhanh, đơn giản. |
| Đọc tài liệu | `pypdf` (PDF), sẵn có cho `.md`/`.txt`/HTML | Ít phụ thuộc. |
| Cắt chunk | tự viết | Hiểu bản chất; ~800 ký tự, overlap ~120. |

Thư viện thêm: `sentence-transformers`, `faiss-cpu`, `pypdf`. Cài chung `.venv`.
`sentence-transformers` dùng lại `torch`/`transformers` đã có nên không nặng thêm nhiều.

## 3. Cấu trúc thư mục (thêm mới)

```
data/
├── knowledge/          # tài liệu NGUỒN (anh bỏ vào đây)
│   ├── owasp/          # .md/.txt/.html tải về
│   ├── manpages/       # nmap.txt, metasploit.txt, burp...
│   └── books/          # .pdf (chỉ tài liệu anh có quyền dùng)
└── rag_index/          # chỉ mục FAISS + metadata (KHÔNG commit)
    ├── luna.faiss
    └── luna_meta.json

src/luna/rag/
├── __init__.py
├── embed.py            # nạp embedding model, hàm encode()
├── chunk.py            # đọc file -> chunk kèm nguồn
├── store.py            # build/load FAISS, search(query, k)
└── retrieve.py         # ghép ngữ cảnh + prompt cho Luna

scripts/
├── build_index.py      # quét data/knowledge -> dựng data/rag_index
└── ask_rag.py          # hỏi thử RAG ngoài luồng chat (để test)
```

## 4. Lộ trình (mỗi bước chạy được & kiểm chứng được)

- **R1 — Hiểu embedding + FAISS (demo tí hon).** Cài thư viện; dựng chỉ mục cho ~6
  câu; hỏi thử để *thấy* semantic search hoạt động. → `guides/rag_step1_demo.md`
- **R2 — Cắt chunk + dựng chỉ mục thật.** Viết `chunk.py`, `embed.py`, `store.py`,
  `build_index.py`. Bỏ vài tài liệu nhỏ vào `data/knowledge/`, dựng chỉ mục, tìm thử.
- **R3 — Nối vào Luna.** `retrieve.py` lấy top-k, chèn vào system prompt kèm nguồn;
  Luna trả lời có trích nguồn. Test bằng câu hỏi bảo mật.
- **R4 — Mở rộng kho + chất lượng.** Thêm OWASP, man page nmap/metasploit/burp,
  sách; lọc trùng, gắn nhãn nguồn, chỉnh k/độ dài chunk; thêm câu "không thấy trong
  tài liệu thì nói không biết".

## 5. Chống bịa (rất quan trọng cho bảo mật)

- System prompt sẽ ép: *"Chỉ trả lời dựa trên Ngữ cảnh dưới đây. Nếu ngữ cảnh không
  có, nói thẳng là chưa có tài liệu, không được bịa."*
- Luôn kèm **nguồn** (tên file + đoạn) để anh kiểm chứng.
- Đặt ngưỡng điểm: nếu chunk gần nhất vẫn quá thấp (không liên quan) → Luna nói
  "chưa có trong tài liệu của em".

## 6. Ghi chú pháp lý & an toàn

- Sách/tài liệu: chỉ nạp thứ anh **có quyền sử dụng** (mua, tự viết, giấy phép mở).
  Em không hỗ trợ tải lậu. OWASP và man page vốn công khai/giấy phép mở nên thoải mái.
- Nội dung pentest ở đây phục vụ **học tập & phòng thủ**. Giữ đúng ranh giới an toàn
  trong `CLAUDE.md`: Luna giải thích khái niệm/kỹ thuật, không tự động thực thi tấn công.
- `data/knowledge/` và `data/rag_index/` **không commit** (thêm vào `.gitignore`).
```
