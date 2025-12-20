/**
 * Mimi Robot - LED Blink Test
 * Không dùng Serial để test xem có phải lỗi USB
 */

#include <Arduino.h>

// LED_BUILTIN hoặc GPIO 48 (RGB LED trên một số board)
#define LED_PIN 2

void setup() {
    pinMode(LED_PIN, OUTPUT);
}

void loop() {
    digitalWrite(LED_PIN, HIGH);
    delay(500);
    digitalWrite(LED_PIN, LOW);
    delay(500);
}
