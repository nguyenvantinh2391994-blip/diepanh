/**
 * Mimi Robot - WiFi Manager
 * Handles WiFi connection and configuration portal
 */

#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <Preferences.h>
#include "config.h"

class MimiWiFiManager {
public:
    MimiWiFiManager() : connected(false) {}

    bool begin() {
        // Try to connect with saved credentials
        WiFi.mode(WIFI_STA);
        WiFi.setAutoReconnect(true);

        // Load saved credentials
        preferences.begin("mimi-wifi", true);
        String ssid = preferences.getString("ssid", "");
        String password = preferences.getString("password", "");
        preferences.end();

        if (ssid.length() > 0) {
            Serial.printf("[WIFI] Connecting to: %s\n", ssid.c_str());
            WiFi.begin(ssid.c_str(), password.c_str());

            unsigned long startTime = millis();
            while (WiFi.status() != WL_CONNECTED &&
                   millis() - startTime < WIFI_CONNECT_TIMEOUT_MS) {
                delay(500);
                Serial.print(".");
            }
            Serial.println();

            if (WiFi.status() == WL_CONNECTED) {
                connected = true;
                Serial.printf("[WIFI] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
                return true;
            }
        }

        Serial.println("[WIFI] No saved credentials or connection failed");
        return false;
    }

    void startConfigPortal(const char* apName) {
        WiFiManager wm;

        // Custom parameters
        wm.setConfigPortalTimeout(180);  // 3 minutes
        wm.setAPCallback([](WiFiManager* wm) {
            Serial.println("[WIFI] Config portal started");
        });

        wm.setSaveConfigCallback([]() {
            Serial.println("[WIFI] Config saved");
        });

        // Custom HTML styling
        wm.setCustomHeadElement("<style>body{background:#f0f0f0;}"
                                ".c{text-align:center;}"
                                "h1{color:#333;}</style>");

        // Start portal
        bool result = wm.startConfigPortal(apName);

        if (result) {
            // Save credentials
            preferences.begin("mimi-wifi", false);
            preferences.putString("ssid", WiFi.SSID());
            preferences.putString("password", wm.getWiFiPass());
            preferences.end();

            connected = true;
            Serial.println("[WIFI] Connected via portal!");
        } else {
            Serial.println("[WIFI] Config portal timeout");
        }
    }

    bool isConnected() const {
        return WiFi.status() == WL_CONNECTED;
    }

    String getIP() const {
        return WiFi.localIP().toString();
    }

    String getSSID() const {
        return WiFi.SSID();
    }

    int getRSSI() const {
        return WiFi.RSSI();
    }

    void disconnect() {
        WiFi.disconnect(true);
        connected = false;
    }

    void resetCredentials() {
        preferences.begin("mimi-wifi", false);
        preferences.clear();
        preferences.end();
        Serial.println("[WIFI] Credentials cleared");
    }

    // Reconnect if disconnected
    void checkConnection() {
        if (!isConnected() && connected) {
            Serial.println("[WIFI] Connection lost, reconnecting...");
            WiFi.reconnect();

            unsigned long startTime = millis();
            while (!isConnected() && millis() - startTime < 10000) {
                delay(500);
            }

            if (isConnected()) {
                Serial.println("[WIFI] Reconnected!");
            }
        }
    }

private:
    Preferences preferences;
    bool connected;
};

#endif // WIFI_MANAGER_H
