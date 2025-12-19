/**
 * Mimi Robot - Configuration
 */

#ifndef MIMI_CONFIG_H
#define MIMI_CONFIG_H

// ===========================================
// Server Configuration
// ===========================================
#define SERVER_HOST "mimi-server.local"  // Your backend server
#define SERVER_PORT 8080
#define SERVER_PATH "/ws"

// ===========================================
// Hardware Pin Definitions (ESP32-S3-N16R8)
// ===========================================

// I2S Audio Pins (Internal codec)
#define I2S_BCLK_PIN        5
#define I2S_LRCLK_PIN       4
#define I2S_DOUT_PIN        6   // Speaker
#define I2S_DIN_PIN         7   // Microphone

// OLED Display (I2C)
#define OLED_SDA_PIN        8
#define OLED_SCL_PIN        9
#define OLED_ADDR           0x3C
#define OLED_WIDTH          128
#define OLED_HEIGHT         64

// Optional Button
#define BUTTON_PIN          0   // Boot button

// LED Indicator (if available)
#define LED_PIN             48  // RGB LED on some boards

// ===========================================
// Audio Configuration
// ===========================================
#define AUDIO_SAMPLE_RATE   16000
#define AUDIO_BITS          16
#define AUDIO_CHANNELS      1
#define AUDIO_BUFFER_SIZE   1024

// Voice Activity Detection
#define VAD_THRESHOLD       500
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
#define DEBUG_AUDIO         0
#define DEBUG_NETWORK       1
#define DEBUG_DISPLAY       0

#endif // MIMI_CONFIG_H
