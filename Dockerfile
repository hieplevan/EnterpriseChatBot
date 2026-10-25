# Sử dụng Python 3.11 slim để tối ưu dung lượng image và tính tương thích cao với torch/chromadb
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Biến môi trường Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Cài đặt các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt dependencies trước để tận dụng Docker cache layer
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Tạo thư mục data nếu chưa có
RUN mkdir -p /app/data/documents /app/data/vector_db

# Mở cổng Streamlit
EXPOSE 8501

# Healthcheck để kiểm tra container hoạt động
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Lệnh khởi chạy ứng dụng Streamlit Frontend
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

