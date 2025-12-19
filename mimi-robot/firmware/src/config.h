/**
 * Mimi Robot - Configuration
 */

#ifndef MIMI_CONFIG_H
#define MIMI_CONFIG_H

// ===========================================
// Server Configuration
// Thay YOUR_COMPUTER_IP bằng IP máy tính của bạn
// Chạy "ipconfig" trên Windows để xem IP
// ===========================================
#define SERVER_HOST "192.168.1.210"  // IP WiFi adapter của PC
#define SERVER_PORT 8080
#define SERVER_PATH "/ws"

// ===========================================
// Hardware Pin Definitions for XH-S3E-AI_V1.0 Board
// (Xiaozhi AI ESP32-S3-N16R8)
// ===========================================

// OLED Display (I2C) - XH-S3E-AI board (from Keyestudio docs)
#define OLED_SDA_PIN        41  // GPIO 41 = SDA
#define OLED_SCL_PIN        42  // GPIO 42 = SCL
#define OLED_ADDR           0x3C
#define OLED_WIDTH          128
#define OLED_HEIGHT         64

// I2S Speaker Pins (NS4168 amplifier)
#define I2S_BCLK_PIN        15  // Bit Clock for speaker
#define I2S_LRCLK_PIN       16  // Left/Right Clock for speaker
#define I2S_DOUT_PIN        7   // Speaker output (Data Out)

// I2S Microphone Pins (INMP441) - từ tài liệu Keyestudio
#define MIC_WS_PIN          4   // Word Select (GPIO 4)
#define MIC_SCK_PIN         5   // Clock (GPIO 5)
#define MIC_SD_PIN          6   // Data (GPIO 6)

// Buttons on XH-S3E-AI board - từ tài liệu Keyestudio
#define BUTTON_PIN          0   // IO0 - Wake/Interrupt
#define VOLUME_UP_PIN       40  // GPIO 40 - Volume+
#define VOLUME_DOWN_PIN     39  // GPIO 39 - Volume-

// LED Indicator
#define LED_PIN             48  // RGB LED (if available)

// ===========================================
// Audio Configuration
// ===========================================
#define AUDIO_SAMPLE_RATE   16000
#define AUDIO_BITS          16
#define AUDIO_CHANNELS      1
#define AUDIO_BUFFER_SIZE   1024

// Voice Activity Detection
#define VAD_THRESHOLD       50
#define VAD_SILENCE_MS      1500  // Silence duration to stop recording

// ===========================================
// Network Configuration
// ===========================================
#define WIFI_CONNECT_TIMEOUT_MS  10000
#define WIFI_RETRY_DELAY_MS      5000
#define WS_RECONNECT_INTERVAL_MS 5000
#define WS_PING_INTERVAL_MS      30000

// ===========================================
// Mimi Personality
// ===========================================
#define MIMI_NAME           "Mimi"
#define MIMI_WAKE_WORD      "mimi"
#define MIMI_LANGUAGE       "vi-VN"

// ===========================================
// Debug Configuration
// ===========================================
#define DEBUG_AUDIO         1   // Bật debug audio để xem mic có hoạt động
#define DEBUG_NETWORK       1
#define DEBUG_DISPLAY       0

#endif // MIMI_CONFIG_H
