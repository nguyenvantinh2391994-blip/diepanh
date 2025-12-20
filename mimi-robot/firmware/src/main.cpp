/**
 * Mimi Robot - Simple Working Firmware
 * Test từng phần: WiFi -> WebSocket -> Audio
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

// OLED Display
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ===========================================
// Configuration
// ===========================================
#define SERVER_HOST       "192.168.1.210"
#define SERVER_PORT       8080
#define SERVER_PATH       "/ws"

// OLED Display
#define OLED_SDA_PIN      8
#define OLED_SCL_PIN      9
#define OLED_ADDR         0x3C
#define OLED_WIDTH        128
#define OLED_HEIGHT       64

// ===========================================
// Global Objects
// ===========================================
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
WebSocketsClient webSocket;
bool wsConnected = false;
String deviceId = "";

// ===========================================
// Display Functions
// ===========================================
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

void drawHappyFace() {
    display.clearDisplay();
    // Eyes
    display.fillCircle(40, 25, 12, SSD1306_WHITE);
    display.fillCircle(88, 25, 12, SSD1306_WHITE);
    display.fillCircle(37, 22, 3, SSD1306_BLACK);
    display.fillCircle(85, 22, 3, SSD1306_BLACK);
    // Smile
    for (int i = -20; i <= 20; i++) {
        int y = 48 + (i * i) / 40;
        display.drawPixel(64 + i, y, SSD1306_WHITE);
    }
    display.display();
}

// ===========================================
// WebSocket Handler
// ===========================================
void onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("[WS] Disconnected");
            wsConnected = false;
            showStatus("WS Disconnected");
            break;

        case WStype_CONNECTED:
            Serial.println("[WS] Connected!");
            wsConnected = true;
            showStatus("WS Connected!");

            // Send device info
            {
                StaticJsonDocument<200> doc;
                doc["type"] = "device_info";
                doc["device_id"] = deviceId;
                String json;
                serializeJson(doc, json);
                webSocket.sendTXT(json);
            }
            delay(500);
            drawHappyFace();
            break;

        case WStype_TEXT:
            Serial.printf("[WS] Got: %s\n", (char*)payload);
            break;

        default:
            break;
    }
}

// ===========================================
// Setup
// ===========================================
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n================================");
    Serial.println("  MIMI ROBOT - Simple Test");
    Serial.println("================================\n");

    // Device ID
    uint64_t chipId = ESP.getEfuseMac();
    char idBuf[17];
    snprintf(idBuf, 17, "%016llX", chipId);
    deviceId = String(idBuf);
    Serial.printf("Device: %s\n", deviceId.c_str());
    Serial.printf("Free Heap: %d\n", ESP.getFreeHeap());

    // Init Display
    Serial.println("[OLED] Init...");
    Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
    if (display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
        Serial.println("[OLED] OK!");
        showStatus("Mimi Robot", "Starting...");
    } else {
        Serial.println("[OLED] FAILED!");
    }
    delay(500);

    // Init WiFi
    Serial.println("[WIFI] Starting WiFiManager...");
    showStatus("WiFi", "Connecting...");

    WiFi.mode(WIFI_STA);
    WiFiManager wm;
    wm.setConfigPortalTimeout(120);  // 2 minutes
    wm.setConnectTimeout(30);        // 30 seconds

    bool wifiOk = wm.autoConnect("Mimi-Setup", "mimi1234");

    if (!wifiOk) {
        Serial.println("[WIFI] FAILED!");
        showStatus("WiFi FAILED!", "Restart in 5s");
        delay(5000);
        ESP.restart();
    }

    Serial.printf("[WIFI] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    showStatus("WiFi OK!", WiFi.localIP().toString().c_str());
    delay(1000);

    // Init WebSocket
    Serial.printf("[WS] Connecting to %s:%d%s\n", SERVER_HOST, SERVER_PORT, SERVER_PATH);
    showStatus("Connecting to", "Server...");

    webSocket.begin(SERVER_HOST, SERVER_PORT, SERVER_PATH);
    webSocket.onEvent(onWebSocketEvent);
    webSocket.setReconnectInterval(3000);

    // Wait for connection
    Serial.println("[WS] Waiting...");
    unsigned long start = millis();
    while (!wsConnected && millis() - start < 10000) {
        webSocket.loop();
        delay(50);
    }

    if (wsConnected) {
        Serial.println("\n[READY] Mimi is ready!");
        showStatus("READY!", "Mimi Online");
        delay(1000);
        drawHappyFace();
    } else {
        Serial.println("[WS] Timeout - no server");
        showStatus("No Server", SERVER_HOST);
    }

    Serial.printf("\nFree Heap: %d\n", ESP.getFreeHeap());
}

// ===========================================
// Loop
// ===========================================
void loop() {
    webSocket.loop();

    // Test: Send ping every 10 seconds
    static unsigned long lastPing = 0;
    if (wsConnected && millis() - lastPing > 10000) {
        lastPing = millis();
        webSocket.sendTXT("{\"type\":\"ping\"}");
        Serial.println("[WS] Ping sent");
    }

    delay(10);
}
