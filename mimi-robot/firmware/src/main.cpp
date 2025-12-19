/**
 * OLED Test for XH-S3E-AI Board
 * Using GPIO 41 (SCL) and GPIO 42 (SDA)
 */

#include <Arduino.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// OLED pins for XH-S3E-AI board
#define OLED_SDA  42
#define OLED_SCL  41
#define OLED_ADDR 0x3C

Adafruit_SSD1306 display(128, 64, &Wire, -1);
bool oledOK = false;

void setup() {
    // Disable brownout detector
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    delay(3000);

    Serial.println();
    Serial.println("================================");
    Serial.println("  OLED TEST - XH-S3E-AI Board");
    Serial.println("================================");
    Serial.printf("SDA: GPIO %d\n", OLED_SDA);
    Serial.printf("SCL: GPIO %d\n", OLED_SCL);

    // Initialize I2C
    Serial.println("\nInitializing I2C...");
    Wire.begin(OLED_SDA, OLED_SCL);
    delay(100);

    // Scan I2C bus
    Serial.println("Scanning I2C bus...");
    int found = 0;
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("  Found device at 0x%02X\n", addr);
            found++;
        }
    }
    if (found == 0) {
        Serial.println("  No I2C devices found!");
    }

    // Initialize OLED
    Serial.println("\nInitializing OLED...");
    if (display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
        Serial.println("OLED OK!");
        oledOK = true;

        display.clearDisplay();
        display.setTextSize(2);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(20, 10);
        display.println("MIMI");
        display.setTextSize(1);
        display.setCursor(5, 40);
        display.println("Hello Diep Anh!");
        display.display();
    } else {
        Serial.println("OLED FAILED!");
    }

    Serial.println("================================");
}

int count = 0;

void loop() {
    Serial.printf("Count: %d\n", count);

    if (oledOK && count % 2 == 0) {
        display.clearDisplay();
        display.setTextSize(2);
        display.setCursor(20, 5);
        display.println("MIMI");
        display.setTextSize(1);
        display.setCursor(5, 30);
        display.printf("Count: %d", count);
        display.setCursor(5, 45);
        display.println("XH-S3E-AI OK!");
        display.display();
    }

    count++;
    delay(1000);
}
