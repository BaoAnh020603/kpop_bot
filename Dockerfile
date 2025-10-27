# Sử dụng Python 3.13 (hoặc phiên bản bạn đang dùng) dựa trên Debian
FROM python:3.13-slim-buster

# ⭐️ CÀI ĐẶT FFMPEG (Đây là bước khắc phục lỗi chính)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file requirements.txt và cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn của bot
COPY . .

# Thiết lập lệnh chạy bot
CMD ["python", "kpop_radio_bot.py"]
