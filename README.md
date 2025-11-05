# 🎧 Kpop Radio Bot

Bot phát radio K-Pop 24/7 dành cho người yêu âm nhạc Hàn Quốc.  
Hỗ trợ phát nhạc trực tuyến, lệnh điều khiển và hoạt động ổn định trên môi trường server.

## 🚀 Tính năng

- ▶️ Phát radio K-Pop 24/7
- 🎶 Stream chất lượng cao
- 🤖 Tự động reconnect khi mất kết nối
- 🛠 Chạy được trên Replit / VPS / Docker
- 🌐 Keep-alive để hoạt động liên tục

## 📦 Cấu trúc dự án
```
├── Dockerfile
├── apt-packages.txt
├── keep_alive.py
├── kpop_radio_bot.py
└── requirements.txt
```
## 🛠 Cài đặt & chạy

### ✅ Yêu cầu
- Python 3.9+
- FFmpeg
- Telegram Bot Token (nếu dùng Telegram)

### 📥 Clone project
```bash
git clone https://github.com/BaoAnh020603/kpop_bot
cd kpop_bot
```
## 📦 Cài thư viện
```
pip install -r requirements.txt
```
## ▶️ Chạy bot
```
python kpop_radio_bot.py
## 🐳 Chạy bằng Docker
```
docker build -t kpop_radio_bot .
docker run -d kpop_radio_bot
```
## 🌍 Chạy keep-alive (Replit/Render)
```
python keep_alive.py
```
## 🔧 Biến môi trường
```
Biến	Mô tả
BOT_TOKEN	Token bot Telegram
STREAM_URL	URL stream radio K-Pop
```

Lưu ý: tạo file .env để lưu thông tin

## 📚 Công nghệ sử dụng
Python
FFmpeg
Docker (tùy chọn)

## ❤️ Đóng góp
Pull request & báo lỗi luôn được chào đón!

## ⭐ Hãy star repo nếu bạn thích dự án này!
