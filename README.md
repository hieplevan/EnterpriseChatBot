# HỆ THỐNG TRỢ LÝ TRI THỨC DOANH NGHIỆP (ENTERPRISE RAG WORKSPACE)

Hệ thống Trợ lý Tra cứu Tri thức và Giải đáp Pháp lý Doanh nghiệp ứng dụng kiến trúc **RAG Nâng cao (Advanced Retrieval-Augmented Generation)**. Dự án được thiết kế theo chuẩn vòng đời phát triển phần mềm (SDLC), phân tách hoàn toàn giữa **Backend REST API (FastAPI)** và **Frontend Web Chat (Streamlit)** theo phong cách ứng dụng chat hiện đại (Gemini / Zalo), vận hành **100% bảo mật nội bộ (On-premise / Local)** với **Ollama** và **ChromaDB**.

---

## 1. TÍNH NĂNG CỐT LÕI

### 1.1. Công nghệ Tìm kiếm Lai (Hybrid Search) & Tái xếp hạng (Re-Ranking)
* **Dense Retrieval (Ngữ nghĩa):** Sử dụng mô hình nhúng `nomic-embed-text` kết hợp cơ sở dữ liệu vector ChromaDB để nắm bắt ngữ cảnh câu hỏi.
* **Sparse Retrieval (Từ khóa chính xác):** Ứng dụng thuật toán `BM25Okapi` tối ưu hóa cho thuật ngữ pháp lý, mã hiệu văn bản và số tiền phạt.
* **Reciprocal Rank Fusion (RRF):** Hợp nhất kết quả từ Dense và Sparse Search với hệ số điều hòa $k=60$ để loại bỏ nhiễu.
* **Cross-Encoder Re-Ranking:** Tinh chỉnh và chấm điểm độ tương quan thực tế giữa câu hỏi và từng đoạn ngữ cảnh trước khi đưa vào LLM.

### 1.2. Định vị Trích dẫn & Bôi đen Trực tiếp (Exact Grounding Highlighting)
* Trích xuất chính xác 100% tọa độ ký tự (`char_start`, `char_end`) và vị trí dòng (`line_start`, `line_end`) trong tài liệu nguồn.
* Màn hình đối chiếu song song: Nhấn vào bất kỳ trích dẫn nào, hệ thống sẽ mở văn bản gốc và bôi màu trực tiếp đoạn điều khoản liên quan, giúp người dùng kiểm chứng tính xác thực và loại trừ ảo giác (hallucination).

### 1.3. Phân quyền Truy cập Theo Vai trò (Role-Based Access Control - RBAC)
* Tích hợp ma trận kiểm soát truy cập đa cấp:
  * **Quản trị viên (ADMIN):** Toàn quyền xem và cấu hình mọi tài liệu, quản lý người dùng, xem log kiểm toán.
  * **Pháp chế (LEGAL):** Tra cứu toàn bộ luật pháp, nghị định và quy định pháp lý.
  * **Nhân sự (HR):** Tra cứu quy chế, chính sách lương thưởng và phúc lợi nhân sự.
  * **Kế toán (FINANCE):** Tra cứu quy chế chi tiêu, tài chính.
  * **Nhân viên (EMPLOYEE):** Chỉ tiếp cận tài liệu công khai (PUBLIC) và hướng dẫn chung nội bộ (INTERNAL).
* Tài liệu thuộc mức bảo mật cao (CONFIDENTIAL, RESTRICTED) được tự động chặn ngay từ tầng truy vấn vector, ngăn ngừa triệt để rò rỉ dữ liệu giữa các phòng ban.

### 1.4. An toàn Thông tin & Bảo mật (Guardrails & PII Masking)
* **Tự động nhận diện và che giấu dữ liệu nhạy cảm (PII):** Tự động phát hiện và chuyển đổi số CCCD/CMND, số điện thoại di động Việt Nam, email và số thẻ tín dụng thành nhãn mã hóa (`[REDACTED_ID]`, `[REDACTED_PHONE]`) trước khi gửi đến mô hình.
* **Chống tấn công Prompt Injection:** Nhận diện và vô hiệu hóa các câu lệnh cố ý phá vỡ chính sách an toàn (Jailbreak, System Prompt Reveal).

### 1.5. Lưu trữ Dữ liệu Bền vững & Nhật ký Kiểm toán (Persistence & Audit Trail)
* Cơ sở dữ liệu SQLAlchemy (SQLite nội bộ tại `data/enterprise.db`, sẵn sàng kết nối PostgreSQL).
* Quản lý nhiều phiên hội thoại, lưu trữ tin nhắn, ghi nhận đánh giá hài lòng (Thumbs Up / Down) từ người dùng.
* Bảng nhật ký kiểm toán ghi lại đầy đủ thời gian, người dùng, độ trễ xử lý (ms) và các cảnh báo vi phạm.

### 1.6. Kho Văn bản Pháp lý Mẫu Sẵn có
1. **Nghị định 100/2019/NĐ-CP & Nghị định 123/2021/NĐ-CP:** Tra cứu mức phạt vi phạm giao thông đường bộ (vượt đèn đỏ, nồng độ cồn, chạy quá tốc độ, giấy tờ xe máy và ô tô).
2. **Bộ luật Lao động 2019 (Số 45/2019/QH14):** Giờ làm việc, làm thêm giờ, ngày nghỉ lễ tết, thâm niên làm việc.
3. **Nghị định 13/2023/NĐ-CP:** 11 quyền cơ bản của chủ thể dữ liệu cá nhân và quy định bảo vệ dữ liệu.
4. **Luật Doanh nghiệp 2020 (Số 59/2020/QH14):** Quy định thành lập, thời hạn góp vốn, cơ cấu công ty TNHH.


---

## 2. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
d:/Chatbot/
├── backend/                              # REST API Backend (FastAPI)
│   └── app/
│       ├── api/                          # Định tuyến API
│       │   ├── chat.py                   # Xử lý RAG, Streaming SSE, Guardrails
│       │   ├── documents.py              # Quản lý kho tài liệu, Upload, Highlight
│       │   ├── conversations.py          # Quản lý phiên hội thoại bền vững
│       │   ├── audit.py                  # API Nhật ký kiểm toán & Giám sát KPI
│       │   └── evaluation.py             # Đo lường RAG Triad Benchmark
│       ├── db/                           # Cơ sở dữ liệu SQLAlchemy ORM
│       │   ├── models.py                 # Định nghĩa các bảng: User, Message, Audit...
│       │   ├── session.py                # Kết nối DB engine & SessionLocal
│       │   └── init_db.py                # Khởi tạo bảng và nạp 5 tài khoản mẫu
│       ├── schemas/                      # Pydantic Schemas kiểm soát I/O
│       ├── services/                     # Lõi thuật toán RAG
│       │   ├── hybrid_retriever.py       # Hybrid Search (BM25 + ChromaDB RRF + RBAC)
│       │   ├── reranker_service.py       # Cross-Encoder Re-Ranking
│       │   ├── document_service.py       # Bóc tách span ký tự và tạo HTML Highlight
│       │   ├── guardrails_service.py     # Che giấu PII & Chống Prompt Injection
│       │   ├── evaluator_service.py      # Đánh giá Faithfulness & Context Relevance
│       │   └── rag_engine.py             # Điều phối luồng xử lý RAG tổng thể
│       ├── config.py                     # Cấu hình biến môi trường và thư mục
│       └── main.py                       # Điểm khởi chạy FastAPI Server
├── frontend/                             # Giao diện người dùng Web Chat (Streamlit)
│   ├── app.py                            # Giao diện tiếng Việt chuẩn Gemini/Zalo (4 phân hệ)
│   └── client.py                         # HTTP Client giao tiếp với Backend
├── data/
│   ├── documents/                        # Thư mục lưu trữ văn bản nguồn (.md, .txt, .pdf)
│   ├── vector_db/                        # Cơ sở dữ liệu vector ChromaDB
│   └── enterprise.db                     # CSDL SQLite lưu User, Tin nhắn, Audit Log
├── app.py                                # File chuyển tiếp tự động sang frontend/app.py
├── run_full_stack.bat                    # Khởi động cả Backend (8000) và Frontend (8501)
├── run_backend.bat                       # Khởi động riêng Backend FastAPI
├── run_frontend.bat                      # Khởi động riêng Frontend Streamlit
├── start_ollama.bat                      # Khởi động Ollama với cấu hình an toàn cho driver
├── Dockerfile                            # Dockerfile triển khai container
├── docker-compose.yml                    # Cấu hình cụm Docker (Ollama + Web App)
├── requirements.txt                      # Danh sách thư viện Python
└── README.md                             # Tài liệu kỹ thuật dự án
```

---

## 3. HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY

### 3.1. Yêu cầu hệ thống
* Hệ điều hành: Windows 10/11 hoặc Linux / macOS.
* Python: Phiên bản 3.10 trở lên.
* [Ollama](https://ollama.com) đã được cài đặt trên máy.

### 3.2. Cài đặt mô hình ngôn ngữ
Mở Terminal và tải 2 mô hình cần thiết:
```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### 3.3. Cài đặt thư viện Python
Tạo môi trường ảo và cài đặt các phụ thuộc:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3.4. Khởi chạy hệ thống

#### Cách 1: Khởi chạy 1-Click (Khuyên dùng trên Windows)
Click đúp chuột vào file:
```
run_full_stack.bat
```
Hệ thống sẽ tự động bật đồng thời cả Backend FastAPI (cổng 8000) và Frontend Streamlit (cổng 8501).

#### Cách 2: Khởi chạy thủ công qua Terminal
1. Bật máy chủ Backend:
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
2. Bật giao diện Frontend:
```bash
streamlit run frontend/app.py
```
Truy cập ứng dụng tại địa chỉ: `http://localhost:8501`.

---

## 4. TÀI KHOẢN MẪU & PHÂN QUYỀN

Hệ thống được khởi tạo sẵn 5 tài khoản đại diện cho các phòng ban:

| Tên đăng nhập | Tên hiển thị | Vai trò (Role) | Phòng ban | Quyền hạn tài liệu |
| :--- | :--- | :--- | :--- | :--- |
| `admin` | System Administrator | ADMIN | ALL | Toàn quyền xem mọi cấp độ bảo mật, xem công cụ Dev. |
| `legal_counsel` | Trưởng phòng Pháp chế | LEGAL | LEGAL | Xem tài liệu Pháp luật, Nghị định, Hướng dẫn chung. |
| `hr_manager` | Trưởng phòng Nhân sự | HR | HR | Xem Quy chế nội bộ, Chính sách nhân sự, Thông tin chung. |
| `finance_lead` | Kế toán trưởng | FINANCE | FINANCE | Xem Quy định tài chính, chi tiêu, Thông tin chung. |
| `general_staff` | Nhân viên nội bộ | EMPLOYEE | GENERAL | Chỉ xem tài liệu công khai và nội bộ thông thường. |

---

## 5. DANH SÁCH ENDPOINTS API (BACKEND FASTAPI)

Tài liệu Swagger UI tương tác trực tiếp có sẵn tại: `http://127.0.0.1:8000/docs`.

* **Trò chuyện & Tra cứu:**
  * `POST /api/chat`: Xử lý câu hỏi, kiểm tra Guardrails, lọc quyền RBAC và trả về câu trả lời kèm trích dẫn tọa độ.
  * `POST /api/chat/stream`: Trả về dữ liệu dạng Server-Sent Events (SSE) theo thời gian thực.
* **Kho tài liệu:**
  * `GET /api/documents`: Lấy danh sách tài liệu kèm số lượng chunk và cấp độ bảo mật.
  * `POST /api/documents/upload`: Tải lên tệp mới, tự động bóc tách tọa độ và lập chỉ mục tức thì.
  * `GET /api/documents/{name}/highlight`: Trả về HTML văn bản gốc đã bôi vàng đoạn trích dẫn.
  * `DELETE /api/documents/{name}`: Xóa tài liệu khỏi bộ chỉ mục và cơ sở dữ liệu.
* **Quản trị & Kiểm toán:**
  * `GET /api/audit/metrics`: Báo cáo chỉ số KPI vận hành RAG.
  * `GET /api/audit/logs`: Xem lịch sử nhật ký kiểm toán.
  * `POST /api/audit/feedback`: Ghi nhận đánh giá Hài lòng / Chưa chuẩn xác từ người dùng.
* **Đo lường chất lượng:**
  * `POST /api/eval/benchmark`: Chạy bộ đánh giá RAG Triad tự động.
