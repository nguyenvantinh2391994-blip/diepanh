/**
 * Mimi Robot - AI Voice Assistant for Kids
 * A cute AI companion that lives in a stuffed bear
 *
 * Hardware: XH-S3E-AI Board (ESP32-S3-N16R8)
 */

#include <Arduino.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include "config.h"
#include "mimi_state.h"
#include "display_manager.h"
#include "audio_manager.h"
#include "wifi_manager.h"
#include "websocket_client.h"

// HTTP Voice endpoint URL
char httpVoiceUrl[128];

// Global objects
MimiState mimiState;
DisplayManager displayManager;
AudioManager audioManager;
MimiWiFiManager wifiManager;
WebSocketClient wsClient;

// Button handling
volatile bool buttonPressed = false;
unsigned long buttonPressTime = 0;
const unsigned long LONG_PRESS_MS = 3000;

// Task handles
TaskHandle_t audioTaskHandle = NULL;
TaskHandle_t displayTaskHandle = NULL;

// Audio buffer for HTTP mode
uint8_t* httpAudioBuffer = nullptr;
size_t httpAudioSize = 0;
size_t httpAudioBufferSize = 0;  // Actual allocated size
bool httpAudioReady = false;

// Buffer sizes
const size_t PSRAM_BUFFER_SIZE = 32000 * 5;   // 5 seconds with PSRAM
const size_t RAM_BUFFER_SIZE = 16000;         // ~0.5 seconds without PSRAM

// Function declarations
void onWebSocketMessage(const String& message);
void onVoiceData(const uint8_t* data, size_t length);
void audioTask(void* parameter);
void displayTask(void* parameter);
void IRAM_ATTR buttonISR();
void playStartupSound();
void sendVoiceViaHTTP();
void testSpeakerWithHTTP();

void setup() {
    // Disable brownout detector
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    delay(2000);

    Serial.println();
    Serial.println("==========================================");
    Serial.println("  MIMI ROBOT - AI Voice Assistant");
    Serial.println("  Version: 0.1.0");
    Serial.println("==========================================");
    Serial.println();

    // Build HTTP voice URL
    snprintf(httpVoiceUrl, sizeof(httpVoiceUrl), "http://%s:%d/api/voice", SERVER_HOST, SERVER_PORT);
    Serial.printf("[INIT] HTTP Voice URL: %s\n", httpVoiceUrl);

    // Allocate HTTP audio buffer - prefer PSRAM, fallback to smaller RAM buffer
    if (psramFound()) {
        httpAudioBufferSize = PSRAM_BUFFER_SIZE;
        httpAudioBuffer = (uint8_t*)ps_malloc(httpAudioBufferSize);
        Serial.printf("[INIT] Using PSRAM for HTTP audio buffer (%d bytes)\n", httpAudioBufferSize);
    } else {
        httpAudioBufferSize = RAM_BUFFER_SIZE;
        httpAudioBuffer = (uint8_t*)malloc(httpAudioBufferSize);
        Serial.printf("[INIT] Using RAM for HTTP audio buffer (%d bytes)\n", httpAudioBufferSize);
    }

    if (!httpAudioBuffer) {
        // Try even smaller buffer as last resort
        httpAudioBufferSize = 8000;  // 0.25 seconds
        httpAudioBuffer = (uint8_t*)malloc(httpAudioBufferSize);
        if (httpAudioBuffer) {
            Serial.printf("[INIT] Using minimal buffer (%d bytes)\n", httpAudioBufferSize);
        } else {
            Serial.println("[INIT] HTTP audio buffer allocation failed!");
        }
    }

    // Initialize display first (for visual feedback)
    Serial.println("[INIT] Starting display...");
    if (!displayManager.begin()) {
        Serial.println("[INIT] Display init failed!");
    } else {
        displayManager.showBootScreen();
    }

    // Show loading status
    displayManager.showStatus("Khoi dong...");

    // Initialize audio
    Serial.println("[INIT] Starting audio...");
    if (!audioManager.begin()) {
        Serial.println("[INIT] Audio init failed!");
        displayManager.showStatus("Loi audio!");
        // Don't set error state - continue anyway
    } else {
        playStartupSound();
    }
    // Always set voice callback regardless of init result
    audioManager.setVoiceCallback(onVoiceData);

    // Initialize button
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonISR, FALLING);

    // Connect to WiFi
    displayManager.showStatus("Ket noi WiFi...");
    Serial.println("[INIT] Connecting to WiFi...");

    if (!wifiManager.begin()) {
        Serial.println("[INIT] Starting WiFi config portal...");
        displayManager.showStatus("Cau hinh WiFi");
        displayManager.showText("Ket noi WiFi:\nMimi-Setup");
        wifiManager.startConfigPortal("Mimi-Setup");
    }

    if (wifiManager.isConnected()) {
        Serial.printf("[INIT] WiFi connected: %s\n", wifiManager.getIP().c_str());
        displayManager.showStatus("Da ket noi WiFi");

        // Connect to WebSocket server
        displayManager.showStatus("Ket noi server...");
        Serial.println("[INIT] Connecting to server...");

        if (wsClient.begin(SERVER_HOST, SERVER_PORT, SERVER_PATH)) {
            Serial.println("[INIT] Server connected!");
            displayManager.showStatus("San sang!");
            wsClient.setMessageCallback(onWebSocketMessage);
        } else {
            Serial.println("[INIT] Server connection failed");
            displayManager.showStatus("Loi server!");
        }
    } else {
        Serial.println("[INIT] WiFi not connected");
        displayManager.showStatus("Khong co WiFi");
    }

    // Create tasks on different cores
    xTaskCreatePinnedToCore(
        audioTask,
        "AudioTask",
        8192,
        NULL,
        2,
        &audioTaskHandle,
        0  // Core 0
    );

    xTaskCreatePinnedToCore(
        displayTask,
        "DisplayTask",
        4096,
        NULL,
        1,
        &displayTaskHandle,
        1  // Core 1
    );

    // Ready!
    mimiState.setState(MimiState::IDLE);
    displayManager.showFace(DisplayManager::HAPPY);

    Serial.println();
    Serial.println("==========================================");
    Serial.println("  MIMI san sang! Noi 'Mimi oi' de bat dau");
    Serial.println("==========================================");
    Serial.println();
}

void loop() {
    // Handle WebSocket
    wsClient.loop();

    // Check WiFi connection
    static unsigned long lastWifiCheck = 0;
    if (millis() - lastWifiCheck > 30000) {
        wifiManager.checkConnection();
        lastWifiCheck = millis();
    }

    // Handle button press
    if (buttonPressed) {
        buttonPressed = false;
        unsigned long pressDuration = millis() - buttonPressTime;

        if (pressDuration > LONG_PRESS_MS) {
            // Long press: reset WiFi
            Serial.println("[BUTTON] Long press - resetting WiFi");
            displayManager.showStatus("Reset WiFi...");
            wifiManager.resetCredentials();
            ESP.restart();
        } else {
            // Short press: test speaker with HTTP
            Serial.println("[BUTTON] Short press - testing speaker via HTTP");
            if (mimiState.isState(MimiState::IDLE)) {
                displayManager.showStatus("Test loa...");
                testSpeakerWithHTTP();
            }
        }
    }

    // State machine
    switch (mimiState.getState()) {
        case MimiState::IDLE:
            // Check for voice activity (wake word detection could go here)
            if (audioManager.isVoiceDetected()) {
                httpAudioSize = 0;  // Reset audio buffer
                httpAudioReady = false;
                mimiState.setState(MimiState::LISTENING);
                displayManager.showFace(DisplayManager::LISTENING);
                Serial.println("[STATE] Voice detected, now LISTENING");
            }
            break;

        case MimiState::LISTENING:
            // Wait for recording to finish
            if (httpAudioReady) {
                Serial.printf("[STATE] Recording finished with %d bytes\n", httpAudioSize);
                mimiState.setState(MimiState::THINKING);
                displayManager.showFace(DisplayManager::THINKING);
                displayManager.showStatus("Dang xu ly...");

                // Send audio via HTTP (blocking call)
                sendVoiceViaHTTP();
            }
            // Timeout after 30 seconds of listening
            else if (mimiState.getStateTime() > 30000) {
                Serial.println("[STATE] Listening timeout");
                mimiState.setState(MimiState::IDLE);
                displayManager.showFace(DisplayManager::SAD);
                httpAudioSize = 0;
                httpAudioReady = false;
            }
            break;

        case MimiState::THINKING:
            // HTTP processing is synchronous, so we move to SPEAKING immediately
            // This state is mostly unused now but kept for compatibility
            if (mimiState.getStateTime() > 100) {
                // If we're still in THINKING after 100ms, something's wrong
                // sendVoiceViaHTTP should have changed state to SPEAKING
                mimiState.setState(MimiState::IDLE);
                displayManager.showFace(DisplayManager::HAPPY);
            }
            break;

        case MimiState::SPEAKING:
            // Check if playback finished
            if (!audioManager.isPlaying()) {
                mimiState.setState(MimiState::IDLE);
                displayManager.showFace(DisplayManager::HAPPY);
            }
            break;

        case MimiState::ERROR:
            // Show error for a while then recover
            if (mimiState.getStateTime() > 5000) {
                mimiState.setState(MimiState::IDLE);
                displayManager.showFace(DisplayManager::HAPPY);
            }
            break;
    }

    delay(10);
}

// Audio task - handles recording and playback
void audioTask(void* parameter) {
    while (true) {
        if (mimiState.isState(MimiState::LISTENING)) {
            audioManager.update();
        }

        if (mimiState.isState(MimiState::SPEAKING)) {
            audioManager.playbackUpdate();
        }

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

// Display task - handles animations
void displayTask(void* parameter) {
    while (true) {
        displayManager.update();
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

// Button interrupt
void IRAM_ATTR buttonISR() {
    buttonPressTime = millis();
    buttonPressed = true;
}

// WebSocket message handler
void onWebSocketMessage(const String& message) {
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (error) {
        Serial.printf("[WS] JSON parse error: %s\n", error.c_str());
        return;
    }

    const char* type = doc["type"];

    if (strcmp(type, "text") == 0) {
        // Text response from AI
        const char* text = doc["text"];
        if (text) {
            Serial.printf("[AI] Response: %s\n", text);
            displayManager.showText(text);
        }
    }
    else if (strcmp(type, "audio") == 0) {
        // Audio response (base64 encoded)
        const char* audioData = doc["data"];
        if (audioData) {
            mimiState.setState(MimiState::SPEAKING);
            displayManager.showFace(DisplayManager::TALKING);
            audioManager.playBase64Audio(audioData);
        }
    }
    else if (strcmp(type, "emotion") == 0) {
        // Change face expression
        const char* emotion = doc["emotion"];
        if (emotion) {
            if (strcmp(emotion, "happy") == 0) {
                displayManager.showFace(DisplayManager::HAPPY);
            } else if (strcmp(emotion, "sad") == 0) {
                displayManager.showFace(DisplayManager::SAD);
            } else if (strcmp(emotion, "surprised") == 0) {
                displayManager.showFace(DisplayManager::SURPRISED);
            } else if (strcmp(emotion, "love") == 0) {
                displayManager.showFace(DisplayManager::LOVE);
            }
        }
    }
    else if (strcmp(type, "command") == 0) {
        // System commands
        const char* cmd = doc["command"];
        if (cmd) {
            if (strcmp(cmd, "restart") == 0) {
                ESP.restart();
            } else if (strcmp(cmd, "reset_wifi") == 0) {
                wifiManager.resetCredentials();
                ESP.restart();
            }
        }
    }
}

// Voice data callback - accumulates audio for HTTP sending
void onVoiceData(const uint8_t* data, size_t length) {
    // Check for end-of-speech signal (0xFFFFFFFF)
    if (length == 4 && data[0] == 0xFF && data[1] == 0xFF &&
        data[2] == 0xFF && data[3] == 0xFF) {
        httpAudioReady = true;
        Serial.printf("[AUDIO] Recording complete, %d bytes ready for HTTP\n", httpAudioSize);
        return;
    }

    // Accumulate audio data
    if (httpAudioBuffer && httpAudioSize + length < httpAudioBufferSize) {
        memcpy(httpAudioBuffer + httpAudioSize, data, length);
        httpAudioSize += length;
    }
}

// Send voice via HTTP and play response
void sendVoiceViaHTTP() {
    if (!httpAudioBuffer || httpAudioSize == 0) {
        Serial.println("[HTTP] No audio data to send");
        return;
    }

    Serial.printf("[HTTP] Sending %d bytes of audio to %s\n", httpAudioSize, httpVoiceUrl);

    HTTPClient http;
    http.begin(httpVoiceUrl);
    http.addHeader("Content-Type", "application/octet-stream");
    http.setTimeout(30000);  // 30 second timeout

    int httpCode = http.POST(httpAudioBuffer, httpAudioSize);

    Serial.printf("[HTTP] Response code: %d\n", httpCode);

    if (httpCode == HTTP_CODE_OK) {
        // Get response audio
        int len = http.getSize();
        Serial.printf("[HTTP] Received %d bytes of audio response\n", len);

        if (len > 0) {
            WiFiClient* stream = http.getStreamPtr();

            // Read audio data into playback buffer
            uint8_t* responseBuffer = (uint8_t*)ps_malloc(len);
            if (responseBuffer) {
                int bytesRead = stream->readBytes(responseBuffer, len);
                Serial.printf("[HTTP] Read %d bytes into buffer\n", bytesRead);

                if (bytesRead > 0) {
                    mimiState.setState(MimiState::SPEAKING);
                    displayManager.showFace(DisplayManager::TALKING);
                    audioManager.playRawAudio(responseBuffer, bytesRead);
                }

                free(responseBuffer);
            } else {
                Serial.println("[HTTP] Failed to allocate response buffer");
            }
        }
    } else {
        Serial.printf("[HTTP] Error: %s\n", http.errorToString(httpCode).c_str());
        mimiState.setState(MimiState::IDLE);
        displayManager.showFace(DisplayManager::SAD);
    }

    http.end();

    // Reset audio buffer
    httpAudioSize = 0;
    httpAudioReady = false;
}

// Test speaker by fetching audio from server
void testSpeakerWithHTTP() {
    char testUrl[128];
    snprintf(testUrl, sizeof(testUrl), "http://%s:%d/api/test-speak", SERVER_HOST, SERVER_PORT);

    Serial.printf("[TEST] Fetching test audio from %s\n", testUrl);

    HTTPClient http;
    http.begin(testUrl);
    http.setTimeout(30000);

    int httpCode = http.GET();

    if (httpCode == HTTP_CODE_OK) {
        int len = http.getSize();
        Serial.printf("[TEST] Received %d bytes of test audio\n", len);

        if (len > 0) {
            WiFiClient* stream = http.getStreamPtr();
            uint8_t* audioData = (uint8_t*)ps_malloc(len);

            if (audioData) {
                stream->readBytes(audioData, len);
                audioManager.playRawAudio(audioData, len);
                mimiState.setState(MimiState::SPEAKING);
                displayManager.showFace(DisplayManager::TALKING);
                free(audioData);
            }
        }
    } else {
        Serial.printf("[TEST] Error: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();
}

// Play startup melody
void playStartupSound() {
    // Simple startup sound using I2S
    const int melody[] = {523, 659, 784, 1047};
    const int durations[] = {150, 150, 150, 300};

    int16_t buffer[256];

    for (int note = 0; note < 4; note++) {
        int samples = (AUDIO_SAMPLE_RATE * durations[note]) / 1000;
        int pos = 0;

        while (pos < samples) {
            int toWrite = min(256, samples - pos);

            for (int i = 0; i < toWrite; i++) {
                float t = (float)(pos + i) / AUDIO_SAMPLE_RATE;
                buffer[i] = (int16_t)(20000 * sin(2.0 * M_PI * melody[note] * t));
            }

            size_t bytesWritten;
            i2s_write(I2S_NUM_1, buffer, toWrite * sizeof(int16_t),
                      &bytesWritten, portMAX_DELAY);
            pos += toWrite;
        }

        delay(30);
    }
}
