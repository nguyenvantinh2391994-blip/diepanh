# Mimi Robot - Kiến trúc cá nhân hóa lâu dài

## Triết lý thiết kế

```
┌────────────────────────────────────────────────────────────┐
│                    DỮ LIỆU CỦA BẠN                         │
│                                                            │
│  ✅ Chạy 100% trên máy tính của bạn                       │
│  ✅ Không gửi dữ liệu lên cloud                           │
│  ✅ Có thể backup, chuyển máy khác                        │
│  ✅ 10 năm sau vẫn dùng được                              │
│  ✅ Thay đổi AI bất cứ lúc nào                            │
└────────────────────────────────────────────────────────────┘
```

## Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                     MÁY TÍNH CỦA BẠN                            │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Ollama    │    │   Mimi      │    │   Memory Database   │ │
│  │  (AI Local) │◄──►│   Server    │◄──►│   (SQLite/JSON)     │ │
│  │             │    │             │    │                     │ │
│  │ - Llama 3   │    │ - Voice     │    │ - Conversations     │ │
│  │ - Qwen      │    │ - Logic     │    │ - Child profile     │ │
│  │ - Gemma     │    │ - Memory    │    │ - Preferences       │ │
│  └─────────────┘    └──────┬──────┘    │ - Stories told      │ │
│                            │           │ - Milestones        │ │
│        100% OFFLINE        │           └─────────────────────┘ │
│        100% PRIVATE        │                                   │
│                      ┌─────▼─────┐                             │
└──────────────────────│   WiFi    │─────────────────────────────┘
                       └─────┬─────┘
                             │
                       ┌─────▼─────┐
                       │  Robot    │
                       │  Mimi     │
                       │ (Gấu bông)│
                       └───────────┘
```

## Dữ liệu được lưu trữ

### 1. Hồ sơ của bé (child_profile)
```json
{
  "name": "Bông",
  "nickname": "Bông bé",
  "birthday": "2020-05-15",
  "age_updated": "2024-01-01",
  "gender": "female",
  "personality_notes": [
    "Thích hỏi 'tại sao'",
    "Hay cười khi nghe chuyện vui",
    "Sợ sấm sét"
  ]
}
```

### 2. Sở thích & Không thích
```json
{
  "likes": [
    {"item": "kem dâu", "discovered": "2024-01-15", "strength": 5},
    {"item": "công chúa Elsa", "discovered": "2024-02-01", "strength": 5},
    {"item": "màu hồng", "discovered": "2024-01-20", "strength": 4},
    {"item": "nhảy múa", "discovered": "2024-03-01", "strength": 4}
  ],
  "dislikes": [
    {"item": "rau", "discovered": "2024-01-10", "strength": 3},
    {"item": "đi ngủ sớm", "discovered": "2024-02-15", "strength": 2}
  ]
}
```

### 3. Cột mốc phát triển (milestones)
```json
{
  "milestones": [
    {
      "date": "2024-01-15",
      "type": "first_conversation",
      "note": "Lần đầu nói chuyện với Mimi"
    },
    {
      "date": "2024-03-20",
      "type": "learned_counting",
      "note": "Bé đếm được từ 1-20"
    },
    {
      "date": "2024-06-01",
      "type": "first_story",
      "note": "Bé tự kể chuyện cho Mimi nghe"
    }
  ]
}
```

### 4. Lịch sử hội thoại (có thể xem lại)
```json
{
  "conversations": [
    {
      "date": "2024-12-19",
      "messages": [
        {"role": "child", "text": "Mimi ơi, hôm nay con đi học về"},
        {"role": "mimi", "text": "Bông ơi! Hôm nay ở trường có gì vui không?"},
        {"role": "child", "text": "Con được cô khen vì viết đẹp"},
        {"role": "mimi", "text": "Wow! Bông giỏi quá! Mimi tự hào về Bông lắm!"}
      ],
      "mood": "happy",
      "topics": ["school", "achievement"]
    }
  ]
}
```

### 5. Câu chuyện đã kể (không lặp lại)
```json
{
  "stories_told": [
    {"id": "cinderella", "times": 3, "last_told": "2024-12-10"},
    {"id": "three_pigs", "times": 5, "last_told": "2024-12-18"},
    {"id": "custom_bong_adventure", "times": 1, "last_told": "2024-12-15"}
  ]
}
```

## Tính năng cá nhân hóa

### Mimi sẽ nhớ:
| Loại | Ví dụ | Cách sử dụng |
|------|-------|--------------|
| **Tên** | "Bông" | "Bông ơi, chào buổi sáng!" |
| **Tuổi** | 4 tuổi | Điều chỉnh ngôn ngữ phù hợp |
| **Sở thích** | Elsa, màu hồng | "Hôm nay Mimi kể chuyện công chúa Elsa nhé!" |
| **Sợ hãi** | Sấm sét | "Đừng sợ, Mimi ở đây với Bông mà" |
| **Thành tích** | Viết đẹp | "Bông viết đẹp lắm, cô khen rồi mà!" |
| **Gia đình** | Mẹ tên Lan | "Mẹ Lan có khỏe không Bông?" |

### Mimi sẽ phát triển theo bé:
```
Năm 1 (3 tuổi):  Nói đơn giản, kể chuyện ngắn
Năm 2 (4 tuổi):  Dạy đếm số, màu sắc, hát
Năm 3 (5 tuổi):  Câu đố đơn giản, chuyện dài hơn
Năm 4 (6 tuổi):  Giúp học chữ, toán cơ bản
Năm 5 (7 tuổi):  Trò chuyện sâu hơn, giải thích khoa học
...
```

## Backup & Di chuyển

### Export dữ liệu:
```bash
# Xuất toàn bộ ký ức của Mimi
python tools/export_memory.py --output bong_memories_2024.zip
```

### Import vào máy mới:
```bash
# Khi đổi máy tính
python tools/import_memory.py --input bong_memories_2024.zip
```

### Cấu trúc file backup:
```
bong_memories_2024.zip
├── profile.json          # Thông tin bé
├── preferences.json      # Sở thích
├── conversations/        # Lịch sử hội thoại
│   ├── 2024-01.json
│   ├── 2024-02.json
│   └── ...
├── milestones.json       # Cột mốc phát triển
├── stories.json          # Chuyện đã kể
└── settings.json         # Cài đặt Mimi
```

## Thay đổi AI khi cần

```yaml
# config.yaml - Dễ dàng chuyển đổi

ai:
  # Lựa chọn 1: Ollama (chạy local, miễn phí)
  provider: "ollama"
  model: "llama3.2"

  # Lựa chọn 2: Nếu muốn dùng cloud
  # provider: "anthropic"
  # model: "claude-3-5-sonnet"

  # Lựa chọn 3: Trong tương lai
  # provider: "future_ai"
  # model: "super_model_2030"
```

## Timeline sử dụng dự kiến

```
2024: Bé 3 tuổi - Bắt đầu dùng Mimi
      └── Mimi học tên, sở thích cơ bản

2025: Bé 4 tuổi - Mimi đã quen bé
      └── Nhớ hàng trăm cuộc hội thoại
      └── Biết bé thích gì, sợ gì

2026: Bé 5 tuổi - Mimi như người bạn thân
      └── Kể chuyện theo sở thích bé
      └── Nhớ các sự kiện quan trọng

2028: Bé 7 tuổi - Upgrade phần cứng
      └── Thay ESP32 mới, giữ nguyên ký ức
      └── Mimi vẫn nhớ mọi thứ

2030: Bé 9 tuổi - Có thể đọc lại
      └── "Mimi, ngày xưa con hay nói gì?"
      └── Xem lại hành trình lớn lên
```
