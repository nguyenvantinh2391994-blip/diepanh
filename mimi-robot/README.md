# 🧸 Mimi Robot - Bạn đồng hành AI cho bé

Robot đối thoại bằng giọng nói, được thiết kế để trở thành người bạn thông minh cho trẻ em.

## Tính năng chính

- **Trò chuyện tự nhiên**: Sử dụng AI để hiểu và phản hồi giọng nói
- **Trí nhớ cá nhân**: Nhớ tên bé, sở thích, các cuộc trò chuyện trước
- **Tính cách Mimi**: Nhân vật dễ thương, vui vẻ, phù hợp với trẻ em
- **Màn hình biểu cảm**: Hiển thị cảm xúc trên OLED 0.96"
- **Dễ nâng cấp**: Kiến trúc module, có thể thay đổi phần cứng/phần mềm

## Phần cứng

- **Board**: MINI ESP32-S3-N16R8 V1
- **CPU**: Dual-core Xtensa LX7 @ 240MHz
- **RAM**: 512KB SRAM + 8MB PSRAM
- **Flash**: 16MB
- **Display**: OLED 0.96" (SSD1306)
- **Audio**: Microphone + Speaker tích hợp
- **Kết nối**: WiFi 802.11 b/g/n + Bluetooth 5.0

## Cấu trúc dự án

```
mimi-robot/
├── firmware/          # Code cho ESP32-S3
│   ├── src/           # Source code chính
│   ├── lib/           # Thư viện
│   └── include/       # Header files
├── backend/           # Server xử lý AI
│   ├── src/           # Source code
│   └── config/        # Cấu hình
├── docs/              # Tài liệu
└── tools/             # Công cụ hỗ trợ
```

## Kiến trúc hệ thống

```
┌─────────────────┐     WiFi      ┌─────────────────┐
│   ESP32-S3      │◄────────────►│   Backend       │
│   (Mimi Robot)  │               │   Server        │
├─────────────────┤               ├─────────────────┤
│ - Mic/Speaker   │               │ - Speech-to-Text│
│ - OLED Display  │               │ - AI Chat (LLM) │
│ - Audio Process │               │ - Text-to-Speech│
│ - WiFi Client   │               │ - Memory Store  │
└─────────────────┘               └─────────────────┘
```

## Cài đặt

### Firmware (ESP32-S3)
```bash
cd firmware
pio run -t upload
```

### Backend Server
```bash
cd backend
pip install -r requirements.txt
python src/main.py
```

## Cấu hình

1. Copy `config/config.example.yaml` thành `config/config.yaml`
2. Điền WiFi credentials
3. Cấu hình API keys cho AI services

## Roadmap

- [x] v0.1: Kiến trúc cơ bản
- [ ] v0.2: Firmware cơ bản (audio, display, WiFi)
- [ ] v0.3: Backend với AI chat
- [ ] v0.4: Trí nhớ và cá nhân hóa
- [ ] v0.5: Tính cách Mimi
- [ ] v1.0: Phiên bản hoàn chỉnh

## License

MIT License - Dự án mã nguồn mở cho mục đích giáo dục
