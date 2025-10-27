# Dockerfile
# Thay thế: FROM python:3.12-slim-buster (đang gây lỗi)
# Bằng phiên bản Python 3.12 dựa trên Debian Bullseye (ổn định hơn)
FROM python:3.12-slim-bullseye

# ⭐️ CÀI ĐẶT FFMPEG (Lệnh này sẽ hoạt động với Bullseye)
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
