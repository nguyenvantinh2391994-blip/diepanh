/**
 * SUPER SIMPLE TEST - Only Serial
 * No OLED, No WiFi, No Audio
 */

#include <Arduino.h>

void setup() {
    Serial.begin(115200);

    // Wait for serial connection
    delay(3000);

    Serial.println();
    Serial.println("========================");
    Serial.println("  ESP32-S3 ALIVE TEST");
    Serial.println("========================");
    Serial.println("If you see this, ESP32 is working!");
    Serial.println();
}

int count = 0;

void loop() {
    Serial.print("Count: ");
    Serial.println(count++);
    delay(1000);
}
