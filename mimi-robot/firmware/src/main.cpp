/**
 * SUPER SIMPLE TEST - Chỉ in Serial
 */

#include <Arduino.h>

void setup() {
    Serial.begin(115200);
    delay(2000);

    Serial.println();
    Serial.println("==========================");
    Serial.println("  MIMI TEST - HELLO!!");
    Serial.println("==========================");
    Serial.println("ESP32-S3 is working!");
}

int count = 0;

void loop() {
    Serial.print("Mimi: ");
    Serial.println(count++);
    delay(1000);
}
