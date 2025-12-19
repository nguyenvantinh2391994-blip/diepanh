# Hướng dẫn cài đặt Robot Mimi

## Yêu cầu

### Phần cứng
- MINI ESP32-S3-N16R8 V1
- Màn hình OLED 0.96" (tùy chọn)
- Cáp USB Type-C
- Gấu bông để đặt robot vào

### Phần mềm
- PlatformIO (trong VSCode)
- Python 3.9+
- pip

---

## Bước 1: Cài đặt Backend Server

### 1.1 Tạo môi trường Python
```bash
cd mimi-robot/backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows
```

### 1.2 Cài đặt dependencies
```bash
pip install -r requirements.txt
pip install edge-tts openai-whisper
```

### 1.3 Cấu hình
```bash
cp .env.example .env
```

Mở file `.env` và điền API key:
```
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

Hoặc nếu dùng OpenAI:
```
OPENAI_API_KEY=sk-xxxxx
```

Sau đó chỉnh `config/config.yaml`:
```yaml
ai:
  provider: "anthropic"  # hoặc "openai"
```

### 1.4 Chạy server
```bash
cd src
python main.py
```

Server sẽ chạy tại `http://0.0.0.0:8080`

---

## Bước 2: Nạp Firmware cho ESP32-S3

### 2.1 Cài đặt PlatformIO
- Cài VSCode
- Cài extension "PlatformIO IDE"

### 2.2 Mở project firmware
```bash
cd mimi-robot/firmware
```
Mở folder này trong VSCode.

### 2.3 Cấu hình WiFi và Server
Mở file `src/config.h` và chỉnh:
```cpp
#define SERVER_HOST "192.168.1.xxx"  // IP máy tính chạy backend
#define SERVER_PORT 8080
```

### 2.4 Nạp firmware
1. Cắm ESP32-S3 qua USB
2. Nhấn Build (✓) trong PlatformIO
3. Nhấn Upload (→) để nạp

### 2.5 Cấu hình WiFi lần đầu
Khi ESP32 khởi động lần đầu:
1. Tìm mạng WiFi "Mimi-Setup"
2. Kết nối và truy cập `192.168.4.1`
3. Nhập tên và mật khẩu WiFi nhà bạn
4. ESP32 sẽ kết nối và nhớ WiFi

---

## Bước 3: Lắp ráp vào gấu bông

### Vị trí đặt các bộ phận
```
    🧸 Gấu bông
    ┌─────────────────┐
    │   👀  OLED      │ <- Mắt/màn hình
    │                 │
    │   🔊 Speaker    │ <- Bụng (loa)
    │                 │
    │   🎤 Mic        │ <- Ngực (mic)
    │                 │
    │   ⚡ ESP32      │ <- Lưng (board)
    └─────────────────┘
```

### Lưu ý
- Đảm bảo mic không bị bịt
- Loa hướng ra ngoài để nghe rõ
- Có thể mở khóa kéo để sạc/bảo trì

---

## Bước 4: Sử dụng

### Khởi động
1. Bật backend server trên máy tính
2. Cắm nguồn cho gấu bông (USB)
3. Chờ màn hình hiện mặt cười 😊

### Trò chuyện
- Nói "Mimi ơi" hoặc bắt đầu nói
- Mimi sẽ hiển thị mặt lắng nghe 👂
- Chờ Mimi trả lời

### Các mặt biểu cảm
- 😊 Vui vẻ (mặc định)
- 👂 Đang lắng nghe
- 🤔 Đang suy nghĩ
- 😴 Ngủ (sau 5 phút không hoạt động)
- 😍 Yêu thương

---

## Xử lý lỗi thường gặp

### ESP32 không kết nối WiFi
- Kiểm tra mật khẩu WiFi
- Reset và cấu hình lại (giữ nút Boot)

### Không nghe được tiếng
- Kiểm tra kết nối loa
- Tăng âm lượng trong config

### AI không trả lời
- Kiểm tra API key
- Kiểm tra kết nối internet của backend

---

## Nâng cấp

### Thêm tính năng mới
1. Fork repository
2. Thêm code vào `firmware/src/` hoặc `backend/src/`
3. Pull request hoặc giữ riêng

### Thay đổi tính cách Mimi
Chỉnh file `backend/config/config.yaml`:
```yaml
personality:
  system_prompt: |
    Bạn là Mimi...
```

### Đổi giọng nói
```yaml
text_to_speech:
  voice: "vi-VN-NamMinhNeural"  # Giọng nam
```

---

## Liên hệ hỗ trợ

Nếu gặp vấn đề, tạo Issue trên GitHub repository.
