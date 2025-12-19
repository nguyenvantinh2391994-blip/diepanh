/**
 * Mimi Robot - Simple Test Firmware
 * Kiểm tra OLED và Serial
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// OLED Configuration
#define OLED_WIDTH 128
#define OLED_HEIGHT 64
#define OLED_ADDR 0x3C

// Các cấu hình pin I2C phổ biến cho ESP32-S3
#define SDA_PIN_1 8
#define SCL_PIN_1 9
#define SDA_PIN_2 21
#define SCL_PIN_2 22
#define SDA_PIN_3 17
#define SCL_PIN_3 18
#define SDA_PIN_4 41
#define SCL_PIN_4 42

Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);

bool tryOLED(int sda, int scl) {
    Serial.printf("Trying I2C: SDA=%d, SCL=%d... ", sda, scl);

    Wire.end();
    delay(50);
    Wire.begin(sda, scl);
    delay(100);

    Wire.beginTransmission(OLED_ADDR);
    int error = Wire.endTransmission();

    if (error == 0) {
        Serial.printf("Found 0x%02X! ", OLED_ADDR);
        if (display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
            Serial.println("OK!");
            return true;
        }
    }
    Serial.println("FAIL");
    return false;
}

void scanI2C(int sda, int scl) {
    Wire.end();
    Wire.begin(sda, scl);
    delay(100);

    Serial.printf("Scan SDA=%d SCL=%d: ", sda, scl);
    bool found = false;
    for (int addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf("0x%02X ", addr);
            found = true;
        }
    }
    if (!found) Serial.print("none");
    Serial.println();
}

void setup() {
    Serial.begin(115200);
    delay(3000);

    Serial.println("\n\n");
    Serial.println("****************************************");
    Serial.println("*     MIMI ROBOT - TEST FIRMWARE       *");
    Serial.println("****************************************");
    Serial.printf("Chip: %s Rev%d\n", ESP.getChipModel(), ESP.getChipRevision());
    Serial.printf("Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("PSRAM: %d bytes\n", ESP.getPsramSize());
    Serial.println();

    bool oledFound = false;

    // Thử các cấu hình pin
    if (tryOLED(SDA_PIN_1, SCL_PIN_1)) oledFound = true;
    else if (tryOLED(SDA_PIN_2, SCL_PIN_2)) oledFound = true;
    else if (tryOLED(SDA_PIN_3, SCL_PIN_3)) oledFound = true;
    else if (tryOLED(SDA_PIN_4, SCL_PIN_4)) oledFound = true;

    if (!oledFound) {
        Serial.println("\n!!! OLED NOT FOUND - Scanning... !!!\n");
        scanI2C(8, 9);
        scanI2C(21, 22);
        scanI2C(17, 18);
        scanI2C(41, 42);
        scanI2C(1, 2);
        scanI2C(4, 5);
        scanI2C(47, 48);
    } else {
        display.clearDisplay();
        display.setTextSize(2);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(30, 5);
        display.println("MIMI");
        display.setTextSize(1);
        display.setCursor(20, 30);
        display.println("Robot v1.0");
        display.setCursor(10, 45);
        display.println("Xin chao con yeu!");
        display.display();
        Serial.println("\n*** OLED OK! Check display! ***\n");
    }

    Serial.println("Setup done! Loop starting...\n");
}

int counter = 0;

void loop() {
    Serial.printf("[%d] Mimi alive - Heap: %d\n", counter++, ESP.getFreeHeap());
    delay(2000);
}
