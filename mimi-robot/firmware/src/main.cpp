/**
 * Mimi Robot - Simple OLED Test
 * Test display on XH-S3E-AI_V1.0 board
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// OLED pins for XH-S3E-AI board
#define OLED_SDA  42
#define OLED_SCL  41
#define OLED_ADDR 0x3C

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("================================");
    Serial.println("  MIMI OLED TEST - XH-S3E-AI");
    Serial.println("================================");
    Serial.printf("SDA Pin: %d\n", OLED_SDA);
    Serial.printf("SCL Pin: %d\n", OLED_SCL);

    // Initialize I2C
    Serial.println("Initializing I2C...");
    Wire.begin(OLED_SDA, OLED_SCL);
    delay(100);

    // Scan I2C bus
    Serial.println("Scanning I2C bus...");
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("Found device at 0x%02X\n", addr);
        }
    }

    // Initialize OLED
    Serial.println("Initializing OLED...");
    if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
        Serial.println("OLED init FAILED!");
        Serial.println("Check wiring or try different pins");
    } else {
        Serial.println("OLED init SUCCESS!");

        display.clearDisplay();
        display.setTextSize(2);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(20, 10);
        display.println("MIMI");
        display.setTextSize(1);
        display.setCursor(10, 40);
        display.println("Hello Diep Anh!");
        display.display();

        Serial.println("Text displayed on OLED!");
    }

    Serial.println("================================");
    Serial.println("Setup complete!");
}

int count = 0;

void loop() {
    Serial.printf("Running... %d\n", count++);

    // Update display every 2 seconds
    if (count % 2 == 0) {
        display.clearDisplay();
        display.setTextSize(2);
        display.setCursor(20, 10);
        display.println("MIMI");
        display.setTextSize(1);
        display.setCursor(10, 35);
        display.printf("Count: %d", count);
        display.setCursor(10, 50);
        display.println("XH-S3E-AI OK!");
        display.display();
    }

    delay(1000);
}
