/**
 * Mimi Robot - Main Firmware
 * ESP32-S3 Voice Dialogue Robot
 *
 * Author: Mimi Project
 * License: MIT
 */

#include <Arduino.h>
#include "config.h"
#include "wifi_manager.h"
#include "audio_manager.h"
#include "display_manager.h"
#include "websocket_client.h"
#include "mimi_state.h"

// Global managers
MimiWiFiManager wifiManager;
AudioManager audioManager;
DisplayManager displayManager;
WebSocketClient wsClient;
MimiState mimiState;

// Task handles
TaskHandle_t audioTaskHandle = NULL;
TaskHandle_t displayTaskHandle = NULL;
TaskHandle_t networkTaskHandle = NULL;

// Forward declarations
void audioTask(void *parameter);
void displayTask(void *parameter);
void networkTask(void *parameter);
void onVoiceData(const uint8_t* data, size_t length);
void onServerMessage(const String& message);

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n================================");
    Serial.println("   Mimi Robot - Starting up");
    Serial.println("================================\n");

    // Initialize display first for visual feedback
    Serial.println("[BOOT] Initializing display...");
    if (!displayManager.begin()) {
        Serial.println("[ERROR] Display init failed!");
    } else {
        displayManager.showBootScreen();
    }

    // Initialize audio system
    Serial.println("[BOOT] Initializing audio...");
    if (!audioManager.begin()) {
        Serial.println("[ERROR] Audio init failed!");
        displayManager.showError("Audio Error");
    }
    audioManager.setVoiceCallback(onVoiceData);

    // Connect to WiFi
    Serial.println("[BOOT] Connecting to WiFi...");
    displayManager.showStatus("Connecting WiFi...");

    if (!wifiManager.begin()) {
        Serial.println("[WARN] WiFi not configured, starting AP mode");
        displayManager.showStatus("Setup WiFi\n192.168.4.1");
        wifiManager.startConfigPortal("Mimi-Setup");
    }

    if (wifiManager.isConnected()) {
        Serial.printf("[BOOT] WiFi connected: %s\n", wifiManager.getIP().c_str());
        displayManager.showStatus("WiFi OK!");

        // Connect to backend server
        Serial.println("[BOOT] Connecting to server...");
        displayManager.showStatus("Connecting server...");

        wsClient.setMessageCallback(onServerMessage);
        if (wsClient.begin(SERVER_HOST, SERVER_PORT, SERVER_PATH)) {
            Serial.println("[BOOT] Server connected!");
            displayManager.showStatus("Ready!");
        } else {
            Serial.println("[WARN] Server connection failed");
            displayManager.showStatus("Offline mode");
        }
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

    xTaskCreatePinnedToCore(
        networkTask,
        "NetworkTask",
        8192,
        NULL,
        1,
        &networkTaskHandle,
        1  // Core 1
    );

    // Initial state
    mimiState.setState(MimiState::IDLE);
    displayManager.showFace(DisplayManager::HAPPY);

    Serial.println("\n[BOOT] Mimi is ready to chat!");
    Serial.println("================================\n");
}

void loop() {
    // Main loop handles state machine
    switch (mimiState.getState()) {
        case MimiState::IDLE:
            // Waiting for wake word or button press
            break;

        case MimiState::LISTENING:
            // Recording voice input
            break;

        case MimiState::THINKING:
            // Waiting for AI response
            break;

        case MimiState::SPEAKING:
            // Playing audio response
            break;

        case MimiState::ERROR:
            // Handle error state
            delay(3000);
            mimiState.setState(MimiState::IDLE);
            break;
    }

    delay(10);
}

// Audio processing task (Core 0)
void audioTask(void *parameter) {
    while (true) {
        audioManager.update();

        // Check for voice activity
        if (audioManager.isVoiceDetected()) {
            if (mimiState.getState() == MimiState::IDLE) {
                mimiState.setState(MimiState::LISTENING);
                displayManager.showFace(DisplayManager::LISTENING);
            }
        }

        // Check if speaking finished
        if (mimiState.getState() == MimiState::SPEAKING &&
            !audioManager.isPlaying()) {
            mimiState.setState(MimiState::IDLE);
            displayManager.showFace(DisplayManager::HAPPY);
        }

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

// Display update task (Core 1)
void displayTask(void *parameter) {
    while (true) {
        displayManager.update();
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

// Network handling task (Core 1)
void networkTask(void *parameter) {
    while (true) {
        wsClient.loop();

        // Reconnect if disconnected
        if (!wsClient.isConnected() && wifiManager.isConnected()) {
            static unsigned long lastReconnect = 0;
            if (millis() - lastReconnect > 5000) {
                wsClient.reconnect();
                lastReconnect = millis();
            }
        }

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

// Callback when voice data is captured
void onVoiceData(const uint8_t* data, size_t length) {
    if (wsClient.isConnected()) {
        // Send audio data to server
        wsClient.sendBinary(data, length);
    }
}

// Callback when server sends a message
void onServerMessage(const String& message) {
    // Parse JSON message from server
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (error) {
        Serial.printf("[ERROR] JSON parse failed: %s\n", error.c_str());
        return;
    }

    const char* type = doc["type"];

    if (strcmp(type, "audio") == 0) {
        // Received audio response
        const char* audioData = doc["data"];
        mimiState.setState(MimiState::SPEAKING);
        displayManager.showFace(DisplayManager::TALKING);
        audioManager.playBase64Audio(audioData);

    } else if (strcmp(type, "text") == 0) {
        // Received text (for display)
        const char* text = doc["text"];
        displayManager.showText(text);

    } else if (strcmp(type, "emotion") == 0) {
        // Change face expression
        const char* emotion = doc["emotion"];
        displayManager.showFaceByName(emotion);

    } else if (strcmp(type, "thinking") == 0) {
        // AI is processing
        mimiState.setState(MimiState::THINKING);
        displayManager.showFace(DisplayManager::THINKING);

    } else if (strcmp(type, "error") == 0) {
        const char* errorMsg = doc["message"];
        Serial.printf("[ERROR] Server error: %s\n", errorMsg);
        displayManager.showError(errorMsg);
        mimiState.setState(MimiState::ERROR);
    }
}
