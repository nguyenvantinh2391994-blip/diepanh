/**
 * Mimi Robot - WebSocket Client
 * Handles communication with backend server
 */

#ifndef WEBSOCKET_CLIENT_H
#define WEBSOCKET_CLIENT_H

#include <Arduino.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "config.h"

typedef void (*MessageCallback)(const String& message);

class WebSocketClient {
public:
    WebSocketClient() : messageCallback(nullptr), _connected(false) {}

    bool begin(const char* host, uint16_t port, const char* path) {
        serverHost = host;
        serverPort = port;
        serverPath = path;

        webSocket.begin(host, port, path);
        webSocket.onEvent([this](WStype_t type, uint8_t* payload, size_t length) {
            this->onWebSocketEvent(type, payload, length);
        });

        webSocket.setReconnectInterval(WS_RECONNECT_INTERVAL_MS);
        webSocket.enableHeartbeat(WS_PING_INTERVAL_MS, 3000, 2);

        Serial.printf("[WS] Connecting to ws://%s:%d%s\n", host, port, path);

        // Wait for initial connection
        unsigned long startTime = millis();
        while (!_connected && millis() - startTime < 5000) {
            webSocket.loop();
            delay(10);
        }

        return _connected;
    }

    void loop() {
        webSocket.loop();
    }

    void setMessageCallback(MessageCallback callback) {
        messageCallback = callback;
    }

    bool isConnected() const { return _connected; }

    void reconnect() {
        if (!_connected) {
            Serial.println("[WS] Attempting reconnection...");
            webSocket.begin(serverHost.c_str(), serverPort, serverPath.c_str());
        }
    }

    void disconnect() {
        webSocket.disconnect();
        _connected = false;
    }

    // Send text message
    bool sendText(const String& message) {
        if (!_connected) return false;
        return webSocket.sendTXT(message);
    }

    // Send JSON message
    bool sendJson(JsonDocument& doc) {
        if (!_connected) return false;

        String jsonString;
        serializeJson(doc, jsonString);
        return webSocket.sendTXT(jsonString);
    }

    // Send binary data (audio)
    bool sendBinary(const uint8_t* data, size_t length) {
        if (!_connected) return false;
        return webSocket.sendBIN(data, length);
    }

    // Send audio start signal
    void sendAudioStart() {
        StaticJsonDocument<128> doc;
        doc["type"] = "audio_start";
        doc["sample_rate"] = AUDIO_SAMPLE_RATE;
        doc["bits"] = AUDIO_BITS;
        doc["channels"] = AUDIO_CHANNELS;
        sendJson(doc);
    }

    // Send audio end signal
    void sendAudioEnd() {
        StaticJsonDocument<64> doc;
        doc["type"] = "audio_end";
        sendJson(doc);
    }

    // Send device info on connect
    void sendDeviceInfo() {
        StaticJsonDocument<256> doc;
        doc["type"] = "device_info";
        doc["device_id"] = getDeviceId();
        doc["firmware_version"] = FIRMWARE_VERSION;
        doc["chip_model"] = ESP.getChipModel();
        doc["free_heap"] = ESP.getFreeHeap();
        doc["psram_size"] = ESP.getPsramSize();
        sendJson(doc);
    }

private:
    WebSocketsClient webSocket;
    MessageCallback messageCallback;
    bool _connected;
    String serverHost;
    uint16_t serverPort;
    String serverPath;

    static constexpr const char* FIRMWARE_VERSION = "0.1.0";

    String getDeviceId() {
        uint64_t chipId = ESP.getEfuseMac();
        char deviceId[17];
        snprintf(deviceId, 17, "%016llX", chipId);
        return String(deviceId);
    }

    void onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
        switch (type) {
            case WStype_DISCONNECTED:
                Serial.println("[WS] Disconnected");
                _connected = false;
                break;

            case WStype_CONNECTED:
                Serial.printf("[WS] Connected to %s\n", (char*)payload);
                _connected = true;
                // Send device info on connect
                sendDeviceInfo();
                break;

            case WStype_TEXT:
                if (DEBUG_NETWORK) {
                    Serial.printf("[WS] Received: %s\n", (char*)payload);
                }
                if (messageCallback) {
                    messageCallback(String((char*)payload));
                }
                break;

            case WStype_BIN:
                Serial.printf("[WS] Received binary: %u bytes\n", length);
                // Handle binary audio response
                if (messageCallback) {
                    // Wrap binary in JSON for callback
                    StaticJsonDocument<128> doc;
                    doc["type"] = "audio_binary";
                    doc["length"] = length;
                    String msg;
                    serializeJson(doc, msg);
                    messageCallback(msg);
                }
                break;

            case WStype_ERROR:
                Serial.println("[WS] Error occurred");
                break;

            case WStype_PING:
                Serial.println("[WS] Ping");
                break;

            case WStype_PONG:
                Serial.println("[WS] Pong");
                break;

            default:
                break;
        }
    }
};

#endif // WEBSOCKET_CLIENT_H
