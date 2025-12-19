# Hướng Dẫn Nhanh - Windows

## Bạn đã có sẵn:
- ✅ Python
- ✅ Ollama với model qwen2.5:7b

---

## Bước 1: Copy project vào E:\mimi

```
E:\mimi\
└── mimi-robot\
    ├── backend\
    ├── firmware\
    └── scripts\
```

---

## Bước 2: Đảm bảo Ollama đang chạy

1. Mở Ollama (icon trong system tray)
2. Kiểm tra model:
```cmd
ollama list
```
Phải thấy: `qwen2.5:7b`

---

## Bước 3: Chạy Backend Server

### Cách 1: Dùng file .bat (dễ nhất)
```
Double-click vào: E:\mimi\mimi-robot\scripts\start_server.bat
```

### Cách 2: Chạy thủ công
```cmd
E:
cd E:\mimi\mimi-robot\backend

:: Tạo môi trường Python (lần đầu)
python -m venv venv

:: Kích hoạt môi trường
venv\Scripts\activate

:: Cài thư viện (lần đầu)
pip install -r requirements.txt
pip install edge-tts aiohttp

:: Chạy server
cd src
python main.py
```

---

## Bước 4: Kiểm tra server hoạt động

Mở trình duyệt: http://localhost:8080

Phải thấy:
```json
{"status": "ok", "service": "Mimi Robot Backend", "version": "0.1.0"}
```

---

## Bước 5: Test nói chuyện với Mimi

Mở PowerShell/Terminal mới, chạy:

```powershell
# Test gửi tin nhắn
$body = @{
    type = "text"
    text = "Xin chào Mimi"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/test" -Method Post -Body $body -ContentType "application/json"
```

---

## Cấu trúc dữ liệu (sẽ tự tạo)

```
E:\mimi\mimi-robot\backend\
├── data\
│   └── mimi_memory.db    ← Ký ức của Mimi (QUAN TRỌNG!)
└── backups\
    └── mimi_memory_xxx.zip ← Backup ký ức
```

---

## Backup ký ức Mimi

```cmd
cd E:\mimi\mimi-robot\backend\tools
python memory_backup.py export
```

File backup lưu tại: `E:\mimi\mimi-robot\backend\backups\`

---

## Khôi phục ký ức

```cmd
python memory_backup.py import mimi_memory_20241219.zip
```

---

## Xem thống kê

```cmd
python memory_backup.py stats
```

---

## Lỗi thường gặp

### "Ollama not responding"
→ Mở Ollama app trước

### "Model not found"
→ Chạy: `ollama pull qwen2.5:7b`

### "Port 8080 in use"
→ Đóng chương trình khác dùng port 8080
→ Hoặc đổi port trong `config/config.yaml`

---

## Tiếp theo: Nạp firmware cho ESP32

Xem file: `docs/HUONG_DAN_CHI_TIET.md` - Phần 5
