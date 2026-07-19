# GLOSSARY — Từ điển thuật ngữ cho người mới

Tra nhanh khi gặp từ lạ. Giải thích theo kiểu dễ hiểu, không hàn lâm.

**Tensor** — mảng số nhiều chiều (giống list lồng nhau) mà GPU tính rất nhanh. Mọi dữ liệu (chữ, ảnh) đều biến thành tensor để model xử lý.

**Tham số (parameter / weight)** — các con số bên trong model được điều chỉnh khi train. "Model 3B" = 3 tỷ con số. Càng nhiều thường càng thông minh nhưng càng tốn VRAM.

**Gradient** — hướng cần chỉnh mỗi tham số để model bớt sai. "Gradient descent" = đi từng bước nhỏ theo hướng đó.

**Training loop** — vòng lặp: đưa dữ liệu vào → model đoán → so với đáp án đúng → tính sai số (loss) → chỉnh tham số. Lặp hàng nghìn lần.

**Loss** — con số đo model sai bao nhiêu. Train tốt = loss giảm dần.

**Epoch / Step** — *step* là 1 lần cập nhật tham số; *epoch* là 1 lần đi hết toàn bộ dữ liệu.

**Tokenizer** — bộ cắt chữ thành các mảnh (token) mà model hiểu. "Mức ký tự" = mỗi chữ cái là 1 token (đơn giản nhất). "BPE/subword" = cắt theo cụm hay gặp (thật hơn).

**Transformer** — kiến trúc mạng nơ-ron nền tảng của mọi LLM hiện đại. Trái tim là **self-attention**.

**Self-attention** — cơ chế cho mỗi từ "nhìn" các từ khác trong câu để hiểu ngữ cảnh.

**GPT** — loại Transformer chỉ-giải-mã, học đoán từ tiếp theo. Đó là cách nó "sinh chữ".

**LLM (Large Language Model)** — model ngôn ngữ lớn, vd Qwen, Llama, GPT.

**Base model / open-weights** — model có sẵn, trọng số công khai để tải về. Bạn train lại được, chạy offline. Khác với "API" (phải gọi qua mạng, không có weights).

**Fine-tune** — train tiếp một model đã có sẵn trên dữ liệu của bạn để đổi phong cách/kỹ năng. Rẻ hơn train từ 0 rất nhiều.

**LoRA / QLoRA** — cách fine-tune tiết kiệm: chỉ train thêm vài "miếng vá" nhỏ (adapter) thay vì cả model. QLoRA = LoRA + nén 4-bit → vừa VRAM 12GB.

**Quantization (4-bit/8-bit)** — nén tham số về ít bit hơn để đỡ tốn VRAM, đổi lại giảm chút chất lượng.

**Inference** — lúc *dùng* model để sinh câu trả lời (khác với *training*).

**VRAM** — RAM của GPU. RTX 3060 của bạn có 12GB — giới hạn kích thước model chạy được.

**Checkpoint** — file lưu trạng thái model đang train, để dừng/tiếp tục được.

**Persona** — "tính cách" bạn gán cho Luna qua system prompt + dữ liệu fine-tune.

**Tool-calling / skill** — model quyết định gọi một hàm ngoài (tra Google, YouTube...) rồi dùng kết quả. Đây là cách Luna "làm được việc".

**RAG (Retrieval-Augmented Generation)** — "sinh câu trả lời có tra cứu". Trước khi Luna trả lời, ta *tìm* vài đoạn tài liệu liên quan rồi *nhét* vào ngữ cảnh cho model đọc. Nhờ vậy Luna trả lời dựa trên tài liệu thật (có nguồn) thay vì bịa. Không cần train lại model.

**Embedding (vector nhúng)** — biến một đoạn chữ thành một dãy số (vector, vd 768 số) sao cho *hai đoạn ý nghĩa giống nhau thì vector gần nhau*. Đây là "tọa độ ngữ nghĩa" của câu.

**Embedding model** — model chuyên tạo embedding (khác với LLM sinh chữ). Ta dùng bản đa ngữ để câu hỏi tiếng Việt vẫn khớp tài liệu tiếng Anh.

**Chunk (đoạn)** — tài liệu dài được cắt thành các mẩu ~vài trăm chữ. Ta embedding & tìm kiếm theo từng chunk, không theo cả cuốn.

**Overlap (chồng lấn)** — các chunk kề nhau chừa phần gối đầu (vd 50 chữ) để câu không bị cắt cụt giữa ý.

**Vector store / vector DB** — kho lưu các embedding + cho tìm nhanh "vector nào gần vector câu hỏi nhất". Ta dùng **FAISS** (lưu ra file, không cần server).

**Top-k** — số đoạn liên quan nhất lấy về (vd k=4) để đưa cho model.

**Cosine similarity** — cách đo hai vector "gần" nhau cỡ nào (1 = trùng hướng, 0 = không liên quan). Dùng để xếp hạng chunk.

**Semantic search** — tìm theo *ý nghĩa* (qua embedding) thay vì tìm trùng từ khóa. "lỗ hổng chèn mã" vẫn khớp "SQL injection".
