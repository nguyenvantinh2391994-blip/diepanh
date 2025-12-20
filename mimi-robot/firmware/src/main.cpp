/**
 * Mimi Robot - Full Firmware
 * ESP32-S3 with WiFi, WebSocket, Audio, Display
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>

// ESP8266Audio for MP3 playback
#include "AudioFileSource.h"
#include "AudioFileSourceBuffer.h"
#include "AudioGeneratorMP3.h"
#include "AudioOutputI2S.h"

// Display
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// mbedtls for base64 decode
#include "mbedtls/base64.h"

// ===========================================
// Configuration - ĐỔI IP SERVER TẠI ĐÂY
// ===========================================
#define SERVER_HOST       "192.168.1.100"  // IP của máy chạy backend
#define SERVER_PORT       8080
#define SERVER_PATH       "/ws"

// I2S Audio Pins (theo phần cứng CLG AI)
#define I2S_BCLK_PIN      5
#define I2S_LRCLK_PIN     4
#define I2S_DOUT_PIN      6   // Speaker
#define I2S_DIN_PIN       7   // Microphone

// OLED Display
#define OLED_SDA_PIN      8
#define OLED_SCL_PIN      9
#define OLED_ADDR         0x3C
#define OLED_WIDTH        128
#define OLED_HEIGHT       64

// Audio settings
#define AUDIO_SAMPLE_RATE 16000
#define AUDIO_BUFFER_SIZE 1024
#define VAD_THRESHOLD     500
#define VAD_SILENCE_MS    1500

// Buffers
#define MAX_AUDIO_SIZE    (32000 * 10)

// ===========================================
// Custom AudioFileSource for memory buffer
// ===========================================
class AudioFileSourceMemory : public AudioFileSource {
public:
    AudioFileSourceMemory(const void *data, uint32_t len) {
        this->data = (const uint8_t*)data;
        this->len = len;
        this->pos = 0;
    }
    virtual ~AudioFileSourceMemory() {}
    virtual bool open(const char *url) override { return true; }
    virtual uint32_t read(void *dst, uint32_t len) override {
        if (pos >= this->len) return 0;
        uint32_t toRead = (pos + len > this->len) ? (this->len - pos) : len;
        memcpy(dst, this->data + pos, toRead);
        pos += toRead;
        return toRead;
    }
    virtual bool seek(int32_t p, int dir) override {
        if (dir == SEEK_SET) this->pos = p;
        else if (dir == SEEK_CUR) this->pos += p;
        else if (dir == SEEK_END) this->pos = len + p;
        return true;
    }
    virtual bool close() override { return true; }
    virtual bool isOpen() override { return true; }
    virtual uint32_t getSize() override { return len; }
    virtual uint32_t getPos() override { return pos; }
private:
    const uint8_t *data;
    uint32_t len;
    uint32_t pos;
};

// ===========================================
// Global Objects
// ===========================================
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
WebSocketsClient webSocket;

// Audio playback
AudioGeneratorMP3 *mp3 = nullptr;
AudioFileSourceMemory *audioSrc = nullptr;
AudioFileSourceBuffer *audioBuff = nullptr;
AudioOutputI2S *audioOut = nullptr;
uint8_t *audioBuffer = nullptr;
size_t audioBufferSize = 0;
bool audioReady = false;

// Recording
int16_t *micBuffer = nullptr;
uint8_t *recordingBuffer = nullptr;
size_t recordedSize = 0;
bool isRecording = false;
bool voiceDetected = false;
unsigned long lastVoiceTime = 0;

// State
bool wsConnected = false;
String deviceId = "";
unsigned long lastPing = 0;
int talkFrame = 0;

// ===========================================
// Face Drawing
// ===========================================
void drawHappyFace() {
    display.clearDisplay();
    display.fillCircle(40, 25, 12, SSD1306_WHITE);
    display.fillCircle(88, 25, 12, SSD1306_WHITE);
    display.fillCircle(37, 22, 3, SSD1306_BLACK);
    display.fillCircle(85, 22, 3, SSD1306_BLACK);
    for (int i = -20; i <= 20; i++) {
        int y = 48 + (i * i) / 40;
        display.drawPixel(64 + i, y, SSD1306_WHITE);
        display.drawPixel(64 + i, y + 1, SSD1306_WHITE);
    }
    display.display();
}

void drawListeningFace() {
    display.clearDisplay();
    display.fillCircle(40, 25, 14, SSD1306_WHITE);
    display.fillCircle(88, 25, 14, SSD1306_WHITE);
    display.fillCircle(40, 25, 5, SSD1306_BLACK);
    display.fillCircle(88, 25, 5, SSD1306_BLACK);
    display.fillCircle(64, 50, 5, SSD1306_WHITE);
    display.display();
}

void drawThinkingFace() {
    display.clearDisplay();
    display.fillCircle(40, 25, 12, SSD1306_WHITE);
    display.fillCircle(88, 25, 12, SSD1306_WHITE);
    display.fillCircle(44, 21, 4, SSD1306_BLACK);
    display.fillCircle(92, 21, 4, SSD1306_BLACK);
    display.fillCircle(100, 20, 2, SSD1306_WHITE);
    display.fillCircle(108, 15, 3, SSD1306_WHITE);
    display.fillCircle(118, 10, 4, SSD1306_WHITE);
    display.drawLine(54, 50, 74, 50, SSD1306_WHITE);
    display.display();
}

void drawTalkingFace() {
    display.clearDisplay();
    display.fillCircle(40, 25, 12, SSD1306_WHITE);
    display.fillCircle(88, 25, 12, SSD1306_WHITE);
    display.fillCircle(40, 25, 4, SSD1306_BLACK);
    display.fillCircle(88, 25, 4, SSD1306_BLACK);
    int mouthHeight = 5 + (talkFrame % 3) * 3;
    display.fillRoundRect(54, 45, 20, mouthHeight, 3, SSD1306_WHITE);
    display.display();
    talkFrame++;
}

void showStatus(const char* line1, const char* line2 = nullptr) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 20);
    display.println(line1);
    if (line2) {
        display.setCursor(0, 35);
        display.println(line2);
    }
    display.display();
}

// ===========================================
// Audio Functions
// ===========================================
bool initMicrophone() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = AUDIO_SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = AUDIO_BUFFER_SIZE,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_BCLK_PIN,
        .ws_io_num = I2S_LRCLK_PIN,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_DIN_PIN
    };

    if (i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL) != ESP_OK) {
        Serial.println("[MIC] I2S install failed");
        return false;
    }

    if (i2s_set_pin(I2S_NUM_0, &pin_config) != ESP_OK) {
        Serial.println("[MIC] Pin config failed");
        return false;
    }

    // Allocate buffers
    if (psramFound()) {
        micBuffer = (int16_t*)ps_malloc(AUDIO_BUFFER_SIZE * sizeof(int16_t));
        recordingBuffer = (uint8_t*)ps_malloc(MAX_AUDIO_SIZE);
        audioBuffer = (uint8_t*)ps_malloc(MAX_AUDIO_SIZE);
        Serial.println("[MIC] Using PSRAM");
    } else {
        micBuffer = (int16_t*)malloc(AUDIO_BUFFER_SIZE * sizeof(int16_t));
        recordingBuffer = (uint8_t*)malloc(MAX_AUDIO_SIZE / 4);
        audioBuffer = (uint8_t*)malloc(MAX_AUDIO_SIZE / 4);
        Serial.println("[MIC] Using internal RAM");
    }

    if (!micBuffer || !recordingBuffer || !audioBuffer) {
        Serial.println("[MIC] Buffer alloc failed");
        return false;
    }

    Serial.println("[MIC] OK");
    return true;
}

bool initSpeaker() {
    audioOut = new AudioOutputI2S();
    audioOut->SetPinout(I2S_BCLK_PIN, I2S_LRCLK_PIN, I2S_DOUT_PIN);
    audioOut->SetGain(0.8);  // 80% volume
    mp3 = new AudioGeneratorMP3();
    Serial.println("[SPK] OK");
    return true;
}

void playAudioData() {
    if (!audioOut || !mp3 || audioBufferSize == 0) return;

    Serial.printf("[SPK] Playing %d bytes\n", audioBufferSize);

    // Stop current playback
    if (mp3->isRunning()) {
        mp3->stop();
    }

    // Clean up old sources
    if (audioBuff) {
        delete audioBuff;
        audioBuff = nullptr;
    }
    if (audioSrc) {
        delete audioSrc;
        audioSrc = nullptr;
    }

    // Create new sources
    audioSrc = new AudioFileSourceMemory(audioBuffer, audioBufferSize);
    audioBuff = new AudioFileSourceBuffer(audioSrc, 2048);

    if (mp3->begin(audioBuff, audioOut)) {
        Serial.println("[SPK] Playback started");
        drawTalkingFace();
    } else {
        Serial.println("[SPK] Failed to start");
        delete audioBuff;
        delete audioSrc;
        audioBuff = nullptr;
        audioSrc = nullptr;
    }
}

// ===========================================
// WebSocket Handler
// ===========================================
void onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("[WS] Disconnected");
            wsConnected = false;
            showStatus("Disconnected", "Reconnecting...");
            break;

        case WStype_CONNECTED:
            Serial.println("[WS] Connected!");
            wsConnected = true;
            {
                StaticJsonDocument<256> doc;
                doc["type"] = "device_info";
                doc["device_id"] = deviceId;
                doc["firmware"] = "1.0.0";
                String json;
                serializeJson(doc, json);
                webSocket.sendTXT(json);
            }
            drawHappyFace();
            break;

        case WStype_TEXT:
            {
                StaticJsonDocument<512> doc;
                if (deserializeJson(doc, payload)) {
                    Serial.println("[WS] JSON error");
                    return;
                }

                const char* msgType = doc["type"];
                if (!msgType) return;

                if (strcmp(msgType, "welcome") == 0) {
                    Serial.println("[WS] Welcome!");
                    drawHappyFace();
                }
                else if (strcmp(msgType, "thinking") == 0) {
                    Serial.println("[WS] Thinking...");
                    drawThinkingFace();
                }
                else if (strcmp(msgType, "text") == 0) {
                    const char* text = doc["text"];
                    if (text) Serial.printf("[WS] %s\n", text);
                }
                else if (strcmp(msgType, "audio") == 0) {
                    const char* b64 = doc["data"];
                    if (b64) {
                        size_t inLen = strlen(b64);
                        size_t outLen = 0;

                        mbedtls_base64_decode(NULL, 0, &outLen,
                                              (const unsigned char*)b64, inLen);

                        if (outLen > 0 && outLen < MAX_AUDIO_SIZE) {
                            size_t actualLen = 0;
                            int ret = mbedtls_base64_decode(
                                audioBuffer, MAX_AUDIO_SIZE, &actualLen,
                                (const unsigned char*)b64, inLen);

                            if (ret == 0 && actualLen > 0) {
                                audioBufferSize = actualLen;
                                audioReady = true;
                                Serial.printf("[WS] Audio: %d bytes\n", actualLen);
                            }
                        }
                    }
                }
            }
            break;

        case WStype_BIN:
            if (length > 0 && length < MAX_AUDIO_SIZE) {
                memcpy(audioBuffer, payload, length);
                audioBufferSize = length;
                audioReady = true;
                Serial.printf("[WS] Binary: %d bytes\n", length);
            }
            break;

        default:
            break;
    }
}

// ===========================================
// Voice Processing
// ===========================================
void processVoice() {
    size_t bytesRead = 0;
    esp_err_t err = i2s_read(I2S_NUM_0, micBuffer, AUDIO_BUFFER_SIZE * sizeof(int16_t),
                              &bytesRead, pdMS_TO_TICKS(10));

    if (err != ESP_OK || bytesRead == 0) return;

    size_t samples = bytesRead / sizeof(int16_t);

    // VAD
    int32_t sum = 0;
    for (size_t i = 0; i < samples; i++) {
        sum += abs(micBuffer[i]);
    }
    int32_t avg = sum / samples;

    voiceDetected = avg > VAD_THRESHOLD;

    if (voiceDetected) {
        lastVoiceTime = millis();

        if (!isRecording) {
            isRecording = true;
            recordedSize = 0;
            Serial.println("[VOI] Recording...");
            drawListeningFace();

            if (wsConnected) {
                StaticJsonDocument<64> doc;
                doc["type"] = "audio_start";
                doc["sample_rate"] = AUDIO_SAMPLE_RATE;
                String json;
                serializeJson(doc, json);
                webSocket.sendTXT(json);
            }
        }

        // Accumulate
        if (recordedSize + bytesRead < MAX_AUDIO_SIZE) {
            memcpy(recordingBuffer + recordedSize, micBuffer, bytesRead);
            recordedSize += bytesRead;
        }

        // Send to server
        if (wsConnected) {
            webSocket.sendBIN((uint8_t*)micBuffer, bytesRead);
        }

    } else if (isRecording) {
        if (millis() - lastVoiceTime > VAD_SILENCE_MS) {
            isRecording = false;
            Serial.printf("[VOI] Done, %d bytes\n", recordedSize);

            if (wsConnected) {
                StaticJsonDocument<32> doc;
                doc["type"] = "audio_end";
                String json;
                serializeJson(doc, json);
                webSocket.sendTXT(json);
            }

            drawThinkingFace();
        }
    }
}

// ===========================================
// Setup
// ===========================================
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n================================");
    Serial.println("    MIMI ROBOT - v1.0");
    Serial.println("================================\n");

    // Device ID
    uint64_t chipId = ESP.getEfuseMac();
    char idBuf[17];
    snprintf(idBuf, 17, "%016llX", chipId);
    deviceId = String(idBuf);
    Serial.printf("Device: %s\n", deviceId.c_str());

    if (psramFound()) {
        Serial.printf("PSRAM: %d KB\n", ESP.getPsramSize() / 1024);
    }

    // Display
    Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
    if (display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
        Serial.println("[OLED] OK");
        showStatus("Mimi", "Starting...");
    }

    // WiFi
    showStatus("WiFi", "Connecting...");
    WiFi.mode(WIFI_STA);
    WiFiManager wm;
    wm.setConfigPortalTimeout(180);

    if (!wm.autoConnect("Mimi-Setup", "mimi1234")) {
        Serial.println("[WIFI] Failed!");
        showStatus("WiFi Failed!", "Restarting...");
        delay(3000);
        ESP.restart();
    }

    Serial.printf("[WIFI] %s\n", WiFi.localIP().toString().c_str());
    showStatus("WiFi OK", WiFi.localIP().toString().c_str());
    delay(1000);

    // Audio
    showStatus("Audio", "Init...");
    initMicrophone();
    initSpeaker();

    // WebSocket
    showStatus("Server", "Connecting...");
    webSocket.begin(SERVER_HOST, SERVER_PORT, SERVER_PATH);
    webSocket.onEvent(onWebSocketEvent);
    webSocket.setReconnectInterval(5000);

    Serial.printf("[WS] ws://%s:%d%s\n", SERVER_HOST, SERVER_PORT, SERVER_PATH);

    unsigned long start = millis();
    while (!wsConnected && millis() - start < 10000) {
        webSocket.loop();
        delay(10);
    }

    if (wsConnected) {
        showStatus("Ready!", "Noi 'Mimi'");
        delay(1000);
        drawHappyFace();
    } else {
        showStatus("No Server", "Check IP");
    }

    Serial.println("\n[READY] Talk to Mimi!\n");
}

// ===========================================
// Loop
// ===========================================
void loop() {
    webSocket.loop();

    // Audio playback
    if (mp3 && mp3->isRunning()) {
        if (!mp3->loop()) {
            mp3->stop();
            Serial.println("[SPK] Done");
            drawHappyFace();
        } else {
            // Animate talking face
            static unsigned long lastAnim = 0;
            if (millis() - lastAnim > 100) {
                lastAnim = millis();
                drawTalkingFace();
            }
        }
    }

    // Play new audio
    if (audioReady) {
        audioReady = false;
        playAudioData();
    }

    // Voice (when not playing)
    if (!mp3 || !mp3->isRunning()) {
        processVoice();
    }

    // Heartbeat
    if (wsConnected && millis() - lastPing > 30000) {
        lastPing = millis();
        webSocket.sendTXT("{\"type\":\"ping\"}");
    }

    delay(1);
}
