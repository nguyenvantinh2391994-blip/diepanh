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
#include <ArduinoJson.h>

#include "config.h"
#include "mimi_state.h"
#include "display_manager.h"
#include "audio_manager.h"
#include "wifi_manager.h"
#include "websocket_client.h"

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

// Function declarations
void onWebSocketMessage(const String& message);
void onVoiceData(const uint8_t* data, size_t length);
void audioTask(void* parameter);
void displayTask(void* parameter);
void IRAM_ATTR buttonISR();
void playStartupSound();

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
            // Short press: activate listening
            Serial.println("[BUTTON] Short press - activating");
            if (mimiState.isState(MimiState::IDLE)) {
                mimiState.setState(MimiState::LISTENING);
                displayManager.showFace(DisplayManager::LISTENING);
                wsClient.sendAudioStart();
            }
        }
    }

    // State machine
    switch (mimiState.getState()) {
        case MimiState::IDLE:
            // Check for voice activity (wake word detection could go here)
            if (audioManager.isVoiceDetected()) {
                mimiState.setState(MimiState::LISTENING);
                displayManager.showFace(DisplayManager::LISTENING);
                wsClient.sendAudioStart();
            }
            break;

        case MimiState::LISTENING:
            // Listening animation handled by display task
            // Wait at least 3 seconds before checking if recording stopped
            if (!audioManager.isCurrentlyRecording() &&
                mimiState.getStateTime() > 3000) {
                // Recording stopped
                mimiState.setState(MimiState::THINKING);
                displayManager.showFace(DisplayManager::THINKING);
                wsClient.sendAudioEnd();
            }
            break;

        case MimiState::THINKING:
            // Waiting for server response
            // Timeout after 30 seconds
            if (mimiState.getStateTime() > 30000) {
                Serial.println("[STATE] Thinking timeout");
                mimiState.setState(MimiState::IDLE);
                displayManager.showFace(DisplayManager::SAD);
                delay(2000);
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

// Voice data callback - sends audio to server
void onVoiceData(const uint8_t* data, size_t length) {
    if (wsClient.isConnected()) {
        wsClient.sendBinary(data, length);
    }
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
