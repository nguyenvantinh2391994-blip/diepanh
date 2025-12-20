/**
 * Mimi Robot - Super Simple Test
 * Chỉ in Serial để test ESP32 hoạt động
 */

#include <Arduino.h>

void setup() {
    Serial.begin(115200);
    delay(3000);  // Đợi Serial ổn định

    Serial.println();
    Serial.println("================================");
    Serial.println("  MIMI ROBOT - BOOT OK!");
    Serial.println("================================");
    Serial.printf("Chip: %s\n", ESP.getChipModel());
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("Flash: %d MB\n", ESP.getFlashChipSize() / 1024 / 1024);

    if (psramFound()) {
        Serial.printf("PSRAM: %d MB\n", ESP.getPsramSize() / 1024 / 1024);
    } else {
        Serial.println("PSRAM: Not found");
    }

    Serial.println("================================");
    Serial.println("Test OK! ESP32 is working!");
    Serial.println("================================");
}

int count = 0;

void loop() {
    Serial.printf("Mimi count: %d\n", count++);
    delay(2000);
}
