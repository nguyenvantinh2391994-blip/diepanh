/**
 * SUPER SIMPLE TEST - Only Serial
 * With brownout detector disabled
 */

#include <Arduino.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

void setup() {
    // Disable brownout detector
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);

    // Long delay for USB CDC to connect
    delay(5000);

    Serial.println();
    Serial.println("========================");
    Serial.println("  ESP32-S3 ALIVE TEST");
    Serial.println("========================");
    Serial.println("Brownout disabled!");
    Serial.println("If you see this, ESP32 is working!");
    Serial.println();
}

int count = 0;

void loop() {
    Serial.print("Count: ");
    Serial.println(count++);
    delay(1000);
}
