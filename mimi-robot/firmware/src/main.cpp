/**
 * Mimi Robot - Main Firmware
 * AI Voice Companion for Children
 */

#include <Arduino.h>
#include "config.h"
#include "display_manager.h"
#include "wifi_manager.h"
#include "websocket_client.h"
#include "audio_manager.h"
#include "mimi_state.h"

// Global managers
DisplayManager displayManager;
MimiWiFiManager wifiManager;
WebSocketClient wsClient;
AudioManager audioManager;

// State machine
MimiState mimiState;

// Task handles
TaskHandle_t displayTaskHandle = NULL;
TaskHandle_t audioTaskHandle = NULL;
TaskHandle_t networkTaskHandle = NULL;

// Forward declarations
void displayTask(void* parameter);
void audioTask(void* parameter);
void networkTask(void* parameter);
void handleWebSocketMessage(const String& message);
void handleVoiceData(const uint8_t* data, size_t length);

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("================================");
    Serial.println("   MIMI ROBOT - Starting up!");
    Serial.println("================================");

    // Initialize Display (with power-on fix)
    Serial.println("[MAIN] Initializing display...");
    if (!displayManager.begin()) {
        Serial.println("[MAIN] Display init failed! Check OLED connection.");
        // Continue anyway - device can work without display
    } else {
        displayManager.showBootScreen();
    }

    delay(500);

    // Initialize Audio
    Serial.println("[MAIN] Initializing audio...");
    if (!audioManager.begin()) {
        Serial.println("[MAIN] Audio init failed!");
    } else {
        // Set voice callback
        audioManager.setVoiceCallback(handleVoiceData);
    }

    // Initialize WiFi
    Serial.println("[MAIN] Initializing WiFi...");
    displayManager.showStatus("Connecting WiFi...");

    if (!wifiManager.begin()) {
        Serial.println("[MAIN] WiFi not configured, starting setup portal...");
        displayManager.showStatus("Setup WiFi\n192.168.4.1");
        wifiManager.startConfigPortal("Mimi-Setup");
    }

    if (wifiManager.isConnected()) {
        Serial.printf("[MAIN] WiFi connected! IP: %s\n", WiFi.localIP().toString().c_str());
        displayManager.showStatus("WiFi OK!");
        delay(500);

        // Connect to backend
        Serial.println("[MAIN] Connecting to backend...");
        displayManager.showStatus("Connecting server...");

        wsClient.setMessageCallback(handleWebSocketMessage);
        if (wsClient.begin(SERVER_HOST, SERVER_PORT, SERVER_PATH)) {
            Serial.println("[MAIN] Backend connected!");
            displayManager.showStatus("Ready!");
            delay(500);
        } else {
            Serial.println("[MAIN] Backend connection failed!");
            displayManager.showStatus("Server offline\nOffline mode");
            delay(1000);
        }
    }

    // Show happy face - ready to interact
    displayManager.showFace(DisplayManager::HAPPY);
    mimiState.setState(MimiState::IDLE);

    // Create FreeRTOS tasks
    Serial.println("[MAIN] Creating tasks...");

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
        audioTask,
        "AudioTask",
        8192,
        NULL,
        2,
        &audioTaskHandle,
        0  // Core 0
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

    Serial.println("[MAIN] Setup complete!");
    Serial.println("================================");
}

void loop() {
    // Main loop is mostly empty - work is done in tasks
    vTaskDelay(pdMS_TO_TICKS(100));
}

// Display update task
void displayTask(void* parameter) {
    Serial.println("[TASK] Display task started");

    while (true) {
        displayManager.update();
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

// Audio capture task
void audioTask(void* parameter) {
    Serial.println("[TASK] Audio task started");

    while (true) {
        // Update audio (reads mic, detects voice)
        audioManager.update();

        // Update playback if playing
        if (audioManager.isPlaying()) {
            audioManager.playbackUpdate();
        }

        // Handle state transitions based on voice
        if (mimiState.isState(MimiState::IDLE)) {
            if (audioManager.isVoiceDetected()) {
                Serial.println("[AUDIO] Voice detected! Listening...");
                mimiState.setState(MimiState::LISTENING);
                displayManager.showFace(DisplayManager::LISTENING);
                wsClient.sendAudioStart();
            }
        } else if (mimiState.isState(MimiState::LISTENING)) {
            if (!audioManager.isCurrentlyRecording()) {
                // Recording stopped (silence detected)
                Serial.println("[AUDIO] Recording ended, waiting for response...");
                mimiState.setState(MimiState::THINKING);
                displayManager.showFace(DisplayManager::THINKING);
                wsClient.sendAudioEnd();
            }
        }

        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

// Network communication task
void networkTask(void* parameter) {
    Serial.println("[TASK] Network task started");

    while (true) {
        // Handle WebSocket
        if (wsClient.isConnected()) {
            wsClient.loop();
        } else if (wifiManager.isConnected()) {
            // Try to reconnect
            Serial.println("[NETWORK] Reconnecting to backend...");
            wsClient.reconnect();
        }

        // Check WiFi connection
        wifiManager.checkConnection();

        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

// Handle voice data callback from AudioManager
void handleVoiceData(const uint8_t* data, size_t length) {
    // Send audio data to server
    if (wsClient.isConnected() && mimiState.isState(MimiState::LISTENING)) {
        wsClient.sendBinary(data, length);
    }
}

// Handle messages from backend
void handleWebSocketMessage(const String& message) {
    Serial.printf("[WS] Received: %s\n", message.c_str());

    // Parse JSON message
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (error) {
        Serial.printf("[WS] JSON parse error: %s\n", error.c_str());
        return;
    }

    const char* type = doc["type"];

    if (strcmp(type, "response") == 0) {
        // AI response with audio
        const char* text = doc["text"];
        const char* audioBase64 = doc["audio"];
        const char* emotion = doc["emotion"] | "happy";

        Serial.printf("[WS] AI says: %s\n", text);

        // Update face emotion
        displayManager.showFaceByName(emotion);
        mimiState.setState(MimiState::SPEAKING);

        // Play audio response
        if (audioBase64 && strlen(audioBase64) > 0) {
            audioManager.playBase64Audio(audioBase64);

            // Wait for playback to finish
            while (audioManager.isPlaying()) {
                audioManager.playbackUpdate();
                vTaskDelay(pdMS_TO_TICKS(10));
            }
        }

        // Return to idle after speaking
        mimiState.setState(MimiState::IDLE);
        displayManager.showFace(DisplayManager::HAPPY);

    } else if (strcmp(type, "emotion") == 0) {
        // Just update emotion
        const char* emotion = doc["emotion"];
        displayManager.showFaceByName(emotion);

    } else if (strcmp(type, "status") == 0) {
        // Status message
        const char* status = doc["status"];
        displayManager.showStatus(status);
    }
}
