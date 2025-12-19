# HƯỚNG DẪN CHẠY MIMI ROBOT - WINDOWS

## YÊU CẦU
- ✅ Windows 10/11
- ✅ Python (bạn đã có)
- ✅ Ollama với qwen2.5:7b (bạn đã có)

---

## BƯỚC 1: TẢI PROJECT

### Cách A: Dùng Git (nếu có)
```cmd
cd /d E:\
git clone https://github.com/nguyenvantinh2391994-blip/diepanh.git
cd diepanh\mimi-robot
```

### Cách B: Tải ZIP
1. Vào: https://github.com/nguyenvantinh2391994-blip/diepanh
2. Nhấn nút xanh "Code" → "Download ZIP"
3. Giải nén vào E:\mimi-robot

---

## BƯỚC 2: CÀI THƯ VIỆN

Mở Command Prompt (cmd), chạy:

```cmd
pip install fastapi uvicorn websockets aiohttp aiosqlite pyyaml edge-tts pydantic
```

Đợi cài xong (khoảng 1-2 phút)

---

## BƯỚC 3: CHẠY SERVER

```cmd
cd /d E:\mimi-robot\backend\src
python main_simple.py
```

Nếu thành công, sẽ thấy:
```
==================================================
🧸 MIMI ROBOT - BACKEND SERVER
==================================================

✅ Database initialized
✅ Ollama connected! Models: ['qwen2.5:7b']

✅ Server ready!
   URL: http://localhost:8080
   WebSocket: ws://localhost:8080/ws
```

---

## BƯỚC 4: TEST THỬ

Mở trình duyệt, vào: http://localhost:8080

Phải thấy:
```json
{"status":"ok","service":"Mimi Robot","version":"1.0.0"}
```

---

## BƯỚC 5: TEST CHAT

Mở Command Prompt MỚI (giữ nguyên cửa sổ server), chạy:

```cmd
cd /d E:\mimi-robot
python test_mimi.py
```

Bạn sẽ có thể chat với Mimi!

---

## LỖI THƯỜNG GẶP

### Lỗi: "Ollama not responding"
→ Mở app Ollama trước khi chạy server

### Lỗi: "Module not found"
→ Chạy lại: `pip install fastapi uvicorn aiohttp aiosqlite pyyaml edge-tts`

### Lỗi: "Port 8080 in use"
→ Đóng chương trình khác dùng port 8080

---

## CẤU TRÚC THƯ MỤC

```
E:\mimi-robot\
├── backend\
│   ├── config\
│   │   └── config.yaml      ← Cấu hình Mimi
│   ├── data\
│   │   └── mimi_memory.db   ← Ký ức của Mimi (tự tạo)
│   └── src\
│       └── main_simple.py   ← Server chính
├── firmware\                 ← Code cho ESP32 (sau này)
├── test_mimi.py              ← Test chat
└── CHAY_NGAY.md              ← File này
```

---

## SAU KHI CHẠY ĐƯỢC

1. Test chat qua `test_mimi.py`
2. Bước tiếp: Nạp firmware cho ESP32
3. Lắp vào gấu bông

Xem tiếp: `docs/HUONG_DAN_CHI_TIET.md`
