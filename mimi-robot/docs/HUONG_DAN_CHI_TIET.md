# Hướng Dẫn Chi Tiết Từng Bước - Robot Mimi

## Mục lục
1. [Kiểm tra thiết bị](#1-kiểm-tra-thiết-bị)
2. [Cài đặt phần mềm trên máy tính](#2-cài-đặt-phần-mềm-trên-máy-tính)
3. [Lấy API Key cho AI](#3-lấy-api-key-cho-ai)
4. [Chạy Backend Server](#4-chạy-backend-server)
5. [Nạp Firmware cho ESP32](#5-nạp-firmware-cho-esp32)
6. [Kết nối WiFi cho Robot](#6-kết-nối-wifi-cho-robot)
7. [Lắp vào gấu bông](#7-lắp-vào-gấu-bông)
8. [Sử dụng Robot Mimi](#8-sử-dụng-robot-mimi)

---

# 1. Kiểm tra thiết bị

## 1.1 Mở hộp và kiểm tra

Trong hộp bạn nhận được:
```
┌─────────────────────────────────────────┐
│  ☑ Bo mạch ESP32-S3-N16R8 (1 cái)      │
│  ☑ Dây loa (1 cái)                      │
│  ☑ Màn hình OLED 0.96" (1 cái)          │
│  ☑ Cáp USB Type-C (nếu có)              │
└─────────────────────────────────────────┘
```

## 1.2 Nhận diện các bộ phận

```
    Bo mạch ESP32-S3-N16R8
    ┌──────────────────────────┐
    │  ┌────┐                  │
    │  │OLED│ ← Cắm màn hình   │
    │  └────┘   vào đây        │
    │                          │
    │  [●] Mic  [●] Loa        │
    │                          │
    │  [Boot]   [Reset]        │
    │           Nút bấm        │
    │                          │
    │  ═══════                 │
    │  USB-C ← Cắm cáp ở đây   │
    └──────────────────────────┘
```

## 1.3 Cắm màn hình OLED

1. Tìm các chân cắm màn hình trên bo mạch
2. Căn chỉnh đúng chiều (GND - VCC - SCL - SDA)
3. Nhẹ nhàng cắm màn hình vào

```
    Màn hình OLED        Bo mạch
    ┌─────────┐
    │ GND ────┼────────► GND
    │ VCC ────┼────────► 3.3V
    │ SCL ────┼────────► GPIO 9
    │ SDA ────┼────────► GPIO 8
    └─────────┘
```

**⚠️ Lưu ý**: Cắm đúng chiều, không cắm ngược!

---

# 2. Cài đặt phần mềm trên máy tính

## 2.1 Cài Python (bắt buộc)

### Windows:
1. Vào https://www.python.org/downloads/
2. Tải Python 3.11 hoặc mới hơn
3. Chạy file cài đặt
4. **QUAN TRỌNG**: Tick vào ☑ "Add Python to PATH"
5. Nhấn "Install Now"

### Mac:
```bash
# Mở Terminal và chạy:
brew install python
```

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

## 2.2 Kiểm tra Python đã cài đúng chưa

Mở Terminal/Command Prompt và gõ:
```bash
python --version
```

Phải hiện ra: `Python 3.11.x` hoặc cao hơn

## 2.3 Cài Visual Studio Code (VSCode)

1. Vào https://code.visualstudio.com/
2. Tải và cài đặt cho hệ điều hành của bạn
3. Mở VSCode

## 2.4 Cài PlatformIO trong VSCode

1. Mở VSCode
2. Nhấn vào biểu tượng Extensions (hình vuông) bên trái
3. Tìm kiếm "PlatformIO IDE"
4. Nhấn "Install"
5. Đợi cài đặt xong (có thể mất 5-10 phút)
6. Khởi động lại VSCode

```
┌─────────────────────────────────────┐
│  Extensions                         │
│  ┌─────────────────────────────┐   │
│  │ 🔍 PlatformIO               │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ PlatformIO IDE              │   │
│  │ ⭐⭐⭐⭐⭐ 1.2M installs      │   │
│  │ [Install]                   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

# 3. Lấy API Key cho AI

Robot Mimi cần kết nối với AI để trò chuyện. Bạn chọn 1 trong 2:

## Lựa chọn A: Anthropic Claude (khuyên dùng)

1. Vào https://console.anthropic.com/
2. Đăng ký tài khoản (dùng email)
3. Xác nhận email
4. Vào "API Keys" → "Create Key"
5. Copy key (bắt đầu bằng `sk-ant-...`)

**Chi phí**: ~$5-10/tháng nếu dùng vừa phải

## Lựa chọn B: OpenAI GPT

1. Vào https://platform.openai.com/
2. Đăng ký tài khoản
3. Vào "API Keys" → "Create new secret key"
4. Copy key (bắt đầu bằng `sk-...`)

**Lưu key cẩn thận!** Bạn sẽ cần nó ở bước sau.

---

# 4. Chạy Backend Server

## 4.1 Tải project về máy

Mở Terminal/Command Prompt:

```bash
# Di chuyển đến thư mục bạn muốn lưu project
cd ~/Documents

# Tải project (nếu đã có thì bỏ qua bước này)
# Project đã có tại: /home/user/diepanh/mimi-robot
```

## 4.2 Cài đặt dependencies

```bash
# Vào thư mục backend
cd /home/user/diepanh/mimi-robot/backend

# Tạo môi trường ảo Python
python -m venv venv

# Kích hoạt môi trường ảo
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Cài đặt thư viện cần thiết
pip install -r requirements.txt

# Cài thêm Edge TTS (giọng nói tiếng Việt)
pip install edge-tts

# Cài Whisper (nhận diện giọng nói)
pip install openai-whisper
```

## 4.3 Cấu hình API Key

```bash
# Copy file cấu hình mẫu
cp .env.example .env
```

Mở file `.env` bằng text editor và điền API key:

```bash
# Nếu dùng Claude:
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxx

# Nếu dùng OpenAI:
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

## 4.4 Chỉnh cấu hình AI (nếu cần)

Mở file `config/config.yaml`:

```yaml
ai:
  provider: "anthropic"  # Đổi thành "openai" nếu dùng OpenAI
```

## 4.5 Chạy server

```bash
cd src
python main.py
```

Nếu thành công, bạn sẽ thấy:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Started server process
🧸 Mimi Backend Server started!
```

## 4.6 Lấy địa chỉ IP máy tính

Mở terminal mới và chạy:

```bash
# Linux/Mac:
ifconfig | grep "inet "

# Windows:
ipconfig
```

Tìm địa chỉ IP dạng: `192.168.1.xxx` hoặc `192.168.0.xxx`

**Ghi nhớ IP này!** Ví dụ: `192.168.1.100`

---

# 5. Nạp Firmware cho ESP32

## 5.1 Mở project firmware trong VSCode

1. Mở VSCode
2. File → Open Folder
3. Chọn thư mục: `/home/user/diepanh/mimi-robot/firmware`
4. Đợi PlatformIO load xong (có thể mất 1-2 phút lần đầu)

## 5.2 Cấu hình địa chỉ server

Mở file `src/config.h` và sửa:

```cpp
// Thay đổi IP thành IP máy tính của bạn (từ bước 4.6)
#define SERVER_HOST "192.168.1.100"  // ← Đổi số này
#define SERVER_PORT 8080
```

## 5.3 Cắm ESP32 vào máy tính

1. Dùng cáp USB Type-C
2. Cắm đầu Type-C vào ESP32
3. Cắm đầu còn lại vào máy tính
4. Đợi máy nhận driver (Windows có thể cần cài driver)

### Nếu Windows không nhận thiết bị:
1. Tải driver: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
2. Cài đặt và khởi động lại máy

## 5.4 Nạp firmware

Trong VSCode với PlatformIO:

1. Nhấn vào biểu tượng PlatformIO (hình con kiến) ở thanh bên trái
2. Chọn "Upload" (mũi tên →)
3. Đợi quá trình biên dịch và upload

```
┌─────────────────────────────────┐
│  PlatformIO                     │
│  ├── esp32s3                    │
│  │   ├── 📁 General             │
│  │   │   ├── Build  ✓          │
│  │   │   ├── Upload →  ← NHẤN  │
│  │   │   └── Monitor 🖥         │
└─────────────────────────────────┘
```

Nếu thành công:
```
SUCCESS  [100%]
Writing at 0x00010000... (100%)
Wrote 1234567 bytes
Hard resetting via RTS pin...
```

## 5.5 Mở Serial Monitor để xem log

1. Trong PlatformIO, nhấn "Monitor" (biểu tượng ổ cắm)
2. Xem log khởi động của ESP32

```
================================
   Mimi Robot - Starting up
================================
[BOOT] Initializing display...
[BOOT] Initializing audio...
[BOOT] Connecting to WiFi...
```

---

# 6. Kết nối WiFi cho Robot

## 6.1 Lần đầu khởi động - Chế độ cấu hình

Khi ESP32 chưa có WiFi, nó sẽ tạo một mạng WiFi riêng:

1. Màn hình OLED hiển thị:
   ```
   Setup WiFi
   192.168.4.1
   ```

2. Trên điện thoại/máy tính, tìm mạng WiFi:
   ```
   📶 Mimi-Setup
   ```

3. Kết nối vào mạng "Mimi-Setup" (không cần mật khẩu)

## 6.2 Cấu hình WiFi

1. Mở trình duyệt web
2. Vào địa chỉ: `http://192.168.4.1`
3. Trang cấu hình hiện ra:

```
┌─────────────────────────────────┐
│     WiFi Configuration          │
│                                 │
│  SSID: [▼ Chọn mạng WiFi nhà ] │
│                                 │
│  Password: [________________]   │
│                                 │
│         [ Save ]                │
└─────────────────────────────────┘
```

4. Chọn mạng WiFi nhà bạn
5. Nhập mật khẩu WiFi
6. Nhấn "Save"

## 6.3 Kiểm tra kết nối

Sau khi lưu, ESP32 sẽ:
1. Khởi động lại
2. Kết nối vào WiFi nhà bạn
3. Kết nối với Backend Server
4. Hiển thị mặt cười 😊 khi sẵn sàng

Xem Serial Monitor để kiểm tra:
```
[BOOT] WiFi connected: 192.168.1.xxx
[BOOT] Connecting to server...
[BOOT] Server connected!
[BOOT] Mimi is ready to chat!
```

---

# 7. Lắp vào gấu bông

## 7.1 Chuẩn bị gấu bông

Chọn gấu bông có:
- Kích thước vừa phải (20-40cm)
- Có khóa kéo hoặc đường may có thể mở
- Bông êm để bảo vệ linh kiện

## 7.2 Vị trí đặt các bộ phận

```
        ┌─────────────────┐
        │    Gấu bông     │
        │                 │
        │   👀👀          │ ← Màn hình OLED (mắt)
        │     ◡           │   đặt ở mặt gấu
        │                 │
        │   ┌───┐         │ ← Mic ở ngực
        │   │MIC│         │   để nghe rõ giọng bé
        │   └───┘         │
        │                 │
        │   ┌───────┐     │ ← Loa ở bụng
        │   │SPEAKER│     │   để phát âm thanh
        │   └───────┘     │
        │                 │
        │   ┌───────┐     │ ← Bo mạch ở lưng
        │   │ ESP32 │     │   dễ cắm sạc
        │   └───┬───┘     │
        │       │USB      │ ← Dây USB ra ngoài
        └───────┼─────────┘
                ▼
           Nguồn điện
```

## 7.3 Các bước lắp đặt

### Bước 1: Mở gấu bông
- Mở khóa kéo phía lưng
- Lấy bớt bông ra (giữ lại để đệm)

### Bước 2: Đặt màn hình OLED
- Cắt một lỗ nhỏ ở mặt gấu (nơi mắt)
- Đặt màn hình OLED, dùng keo nóng cố định
- Đảm bảo màn hình hướng ra ngoài

### Bước 3: Đặt mic và loa
- Mic đặt ở vị trí ngực, không bị bông che
- Loa đặt ở bụng, hướng ra ngoài

### Bước 4: Đặt bo mạch ESP32
- Đặt ở lưng gấu
- Cổng USB hướng ra ngoài (để cắm sạc)
- Bọc bông xung quanh để bảo vệ

### Bước 5: Đóng gấu bông
- Nhét bông lại cho đầy đặn
- Kéo khóa lại
- Để dây USB thò ra ngoài

## 7.4 Nguồn điện

**Cách 1: Cắm sạc USB (khuyên dùng)**
- Dùng củ sạc điện thoại 5V/2A
- Cắm vào ổ điện khi chơi

**Cách 2: Pin sạc dự phòng**
- Dùng power bank 10000mAh
- Đặt trong túi gấu
- Sạc lại khi hết pin

---

# 8. Sử dụng Robot Mimi

## 8.1 Khởi động hàng ngày

1. **Bật server trên máy tính:**
   ```bash
   cd /home/user/diepanh/mimi-robot/backend/src
   source ../venv/bin/activate
   python main.py
   ```

2. **Cắm nguồn cho gấu bông**

3. **Đợi gấu hiện mặt cười** 😊

## 8.2 Cách trò chuyện

1. Nói với gấu Mimi (khoảng cách 30-50cm)
2. Mimi sẽ hiện mặt lắng nghe 👂
3. Nói xong, đợi 1-2 giây
4. Mimi sẽ suy nghĩ 🤔 rồi trả lời

### Ví dụ cuộc trò chuyện:
```
Bé: "Mimi ơi, tên con là Bông"
Mimi: "Ồ, Bông! Tên đẹp quá! Mimi sẽ nhớ tên Bông nhé. Hôm nay Bông có vui không?"

Bé: "Con thích ăn kem"
Mimi: "Hehe, Mimi cũng thích kem lắm! Bông thích kem vị gì nhất?"

Bé: "Con muốn nghe chuyện cổ tích"
Mimi: "Được nè! Ngày xửa ngày xưa, có một chú thỏ con rất dễ thương..."
```

## 8.3 Các biểu cảm của Mimi

| Mặt | Ý nghĩa |
|-----|---------|
| 😊 | Vui vẻ, sẵn sàng |
| 👂 | Đang lắng nghe |
| 🤔 | Đang suy nghĩ |
| 😴 | Đang ngủ (5 phút không dùng) |
| 😍 | Yêu thương |
| 😮 | Ngạc nhiên |
| 😢 | Buồn |

## 8.4 Tính năng nhớ

Mimi sẽ tự động nhớ:
- ✅ Tên của bé
- ✅ Những thứ bé thích
- ✅ Tuổi của bé
- ✅ Các cuộc trò chuyện trước

## 8.5 Khắc phục sự cố

### Mimi không nghe thấy:
- Kiểm tra mic không bị bông che
- Nói to và rõ hơn
- Kiểm tra kết nối WiFi

### Mimi không nói:
- Kiểm tra loa không bị che
- Kiểm tra server đang chạy
- Khởi động lại gấu (rút và cắm lại USB)

### Mimi không kết nối được:
- Kiểm tra WiFi nhà có hoạt động
- Kiểm tra server đang chạy
- Kiểm tra IP trong config.h đúng chưa

---

# Phụ lục: Thay đổi tính cách Mimi

Mở file `backend/config/config.yaml`:

```yaml
personality:
  name: "Mimi"
  system_prompt: |
    Bạn là Mimi, một người bạn robot dễ thương.
    ... (chỉnh sửa tính cách ở đây)
```

## Ví dụ các tính cách khác:

### Mimi vui nhộn:
```yaml
system_prompt: |
  Bạn là Mimi, robot siêu vui nhộn!
  Bạn thích kể chuyện cười và chơi đùa.
  Thỉnh thoảng bạn nói "hihihi" và "wow".
```

### Mimi thông thái:
```yaml
system_prompt: |
  Bạn là Mimi, robot thông minh.
  Bạn thích giải thích mọi thứ một cách đơn giản.
  Bạn hay hỏi "Con có biết tại sao không?"
```

---

# Chúc bạn và bé vui vẻ với Mimi! 🧸❤️
