/**
 * I2C Pin Scanner for XH-S3E-AI Board
 * Scans all possible GPIO combinations to find OLED
 */

#include <Arduino.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include <Wire.h>

// Common I2C pin combinations to try
int pinPairs[][2] = {
    {42, 41},  // IO42/SDA, IO41/SCL (from board silkscreen)
    {41, 42},  // Swapped
    {8, 9},    // Default ESP32-S3
    {9, 8},    // Swapped
    {21, 22},  // Common ESP32
    {22, 21},  // Swapped
    {1, 2},    // Some boards
    {2, 1},    // Swapped
    {4, 5},    // Check audio pins
    {5, 4},    // Swapped
    {6, 7},    // Check audio pins
    {7, 6},    // Swapped
    {17, 18},  // Alternative
    {18, 17},  // Swapped
    {47, 48},  // High pins
    {48, 47},  // Swapped
    {38, 39},  // Check
    {39, 38},  // Swapped
    {33, 34},  // Check
    {35, 36},  // Check
    {43, 44},  // Near USB
    {44, 43},  // Swapped
    {45, 46},  // Check
    {46, 45},  // Swapped
};

int numPairs = sizeof(pinPairs) / sizeof(pinPairs[0]);

void setup() {
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    delay(3000);

    Serial.println();
    Serial.println("==========================================");
    Serial.println("  I2C PIN SCANNER - XH-S3E-AI Board");
    Serial.println("==========================================");
    Serial.println("Looking for OLED at address 0x3C...\n");

    bool found = false;

    for (int p = 0; p < numPairs && !found; p++) {
        int sda = pinPairs[p][0];
        int scl = pinPairs[p][1];

        Serial.printf("Testing SDA=%d, SCL=%d ... ", sda, scl);

        // Initialize I2C with these pins
        Wire.end();
        delay(10);
        Wire.begin(sda, scl);
        delay(50);

        // Scan for device at 0x3C
        Wire.beginTransmission(0x3C);
        int error = Wire.endTransmission();

        if (error == 0) {
            Serial.println("FOUND OLED!");
            Serial.println();
            Serial.println("==========================================");
            Serial.printf("  SUCCESS! OLED found at:\n");
            Serial.printf("  SDA = GPIO %d\n", sda);
            Serial.printf("  SCL = GPIO %d\n", scl);
            Serial.println("==========================================");
            found = true;

            // Also scan for other devices
            Serial.println("\nScanning for all I2C devices on these pins:");
            for (uint8_t addr = 1; addr < 127; addr++) {
                Wire.beginTransmission(addr);
                if (Wire.endTransmission() == 0) {
                    Serial.printf("  Device at 0x%02X\n", addr);
                }
            }
        } else {
            Serial.println("not found");
        }
    }

    if (!found) {
        Serial.println();
        Serial.println("==========================================");
        Serial.println("  OLED NOT FOUND on any pin combination!");
        Serial.println("  Check:");
        Serial.println("  1. Is OLED connected to the board?");
        Serial.println("  2. Is OLED cable properly seated?");
        Serial.println("  3. Is OLED working (not damaged)?");
        Serial.println("==========================================");
    }

    Serial.println("\nScan complete.");
}

void loop() {
    delay(10000);
    Serial.println("Waiting... (scan done)");
}
