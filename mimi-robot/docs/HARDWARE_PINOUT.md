# Sơ đồ chân phần cứng ESP32-S3-N16R8

## Board Layout

```
         ┌─────────────────────────┐
         │    MINI ESP32-S3-N16R8  │
         │         V1 Board        │
         │                         │
USB-C ◄──┤                         │
         │  ┌───────┐              │
         │  │ OLED  │  0.96"       │
         │  │128x64 │  Display     │
         │  └───────┘              │
         │                         │
         │  [MIC]   [SPEAKER]      │
         │                         │
         │  ▪ Boot  ▪ Reset        │
         └─────────────────────────┘
```

## Pin Mapping

### I2S Audio (Built-in Codec)
| Chức năng | GPIO Pin | Ghi chú |
|-----------|----------|---------|
| I2S_BCLK  | GPIO 5   | Bit Clock |
| I2S_LRCLK | GPIO 4   | Word Select |
| I2S_DOUT  | GPIO 6   | Speaker Data |
| I2S_DIN   | GPIO 7   | Microphone Data |

### OLED Display (I2C)
| Chức năng | GPIO Pin | Ghi chú |
|-----------|----------|---------|
| SDA       | GPIO 8   | I2C Data |
| SCL       | GPIO 9   | I2C Clock |
| Address   | 0x3C     | SSD1306 |

### Buttons
| Chức năng | GPIO Pin | Ghi chú |
|-----------|----------|---------|
| Boot      | GPIO 0   | Có thể dùng làm nút nhấn |
| Reset     | EN       | Hardware reset |

### Optional RGB LED
| Chức năng | GPIO Pin | Ghi chú |
|-----------|----------|---------|
| RGB LED   | GPIO 48  | WS2812 (nếu có) |

## Power

- **Input**: 5V qua USB-C
- **Operating**: 3.3V (LDO on-board)
- **Current**: ~150mA typical, ~300mA peak

## Memory

```
Flash: 16MB (QIO)
├── Firmware: ~2MB
├── SPIFFS: ~4MB (cho audio cache)
└── OTA: ~4MB (cho update firmware)

PSRAM: 8MB (OPI)
├── Audio Buffer: ~1MB
└── Heap: ~7MB
```

## Kết nối mở rộng

Các chân GPIO còn trống có thể dùng cho:
- Cảm biến chạm
- LED thêm
- Servo motor (nếu muốn robot cử động)

| GPIO | Khả dụng | Gợi ý sử dụng |
|------|----------|---------------|
| GPIO 1 | ✓ | Touch sensor |
| GPIO 2 | ✓ | LED indicator |
| GPIO 3 | ✓ | Servo PWM |
| GPIO 10-14 | ✓ | Expansion |

## Lưu ý quan trọng

1. **Không dùng GPIO 0** khi boot - dành cho boot mode
2. **GPIO 45, 46** - dành cho PSRAM, không sử dụng
3. **Cấp nguồn ổn định** - dùng nguồn USB chất lượng tốt
4. **Tản nhiệt** - ESP32-S3 có thể nóng khi xử lý nhiều
