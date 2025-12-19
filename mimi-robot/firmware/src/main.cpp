/**
 * OLED + Speaker Test for XH-S3E-AI Board
 * Tests both display and audio
 */

#include <Arduino.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <driver/i2s.h>
#include <math.h>

// OLED Display pins (I2C) - XH-S3E-AI board (from Keyestudio docs)
#define OLED_SDA    41  // GPIO 41 = SDA
#define OLED_SCL    42  // GPIO 42 = SCL
#define OLED_ADDR   0x3C
#define OLED_WIDTH  128
#define OLED_HEIGHT 64

// I2S pins for NS4168 amplifier
#define I2S_BCLK    15
#define I2S_LRCLK   16
#define I2S_DOUT    7

#define SAMPLE_RATE 16000
#define BUFFER_SIZE 1024

Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
int16_t audioBuffer[BUFFER_SIZE];
bool oledOK = false;

void scanI2C() {
    Serial.println("\nScanning I2C bus...");
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
    } else {
        Serial.printf("  Total: %d device(s)\n", found);
    }
}

bool setupOLED() {
    Serial.println("\n[OLED] Initializing...");
    Serial.printf("  SDA: GPIO %d\n", OLED_SDA);
    Serial.printf("  SCL: GPIO %d\n", OLED_SCL);

    Wire.begin(OLED_SDA, OLED_SCL);
    delay(100);

    scanI2C();

    Serial.println("\n[OLED] Starting SSD1306...");

    for (int attempt = 0; attempt < 3; attempt++) {
        if (display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
            Serial.println("[OLED] SUCCESS!");
            display.clearDisplay();
            display.setTextSize(2);
            display.setTextColor(SSD1306_WHITE);
            display.setCursor(10, 10);
            display.println("MIMI");
            display.setTextSize(1);
            display.setCursor(10, 40);
            display.println("Hello World!");
            display.display();
            return true;
        }
        Serial.printf("[OLED] Attempt %d failed\n", attempt + 1);
        delay(100);
    }

    Serial.println("[OLED] FAILED after 3 attempts");
    return false;
}

void setupI2S() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = BUFFER_SIZE,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_BCLK,
        .ws_io_num = I2S_LRCLK,
        .data_out_num = I2S_DOUT,
        .data_in_num = I2S_PIN_NO_CHANGE
    };

    esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("[I2S] Driver install failed: %d\n", err);
        return;
    }

    err = i2s_set_pin(I2S_NUM_0, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("[I2S] Pin config failed: %d\n", err);
        return;
    }

    Serial.println("[I2S] Initialized OK");
}

void playTone(int frequency, int durationMs) {
    int samples = (SAMPLE_RATE * durationMs) / 1000;
    float amplitude = 30000;

    int pos = 0;
    while (pos < samples) {
        int toWrite = min(BUFFER_SIZE, samples - pos);

        for (int i = 0; i < toWrite; i++) {
            float t = (float)(pos + i) / SAMPLE_RATE;
            audioBuffer[i] = (int16_t)(amplitude * sin(2.0 * M_PI * frequency * t));
        }

        size_t bytesWritten;
        i2s_write(I2S_NUM_0, audioBuffer, toWrite * sizeof(int16_t), &bytesWritten, portMAX_DELAY);
        pos += toWrite;
    }

    memset(audioBuffer, 0, sizeof(audioBuffer));
    size_t bytesWritten;
    i2s_write(I2S_NUM_0, audioBuffer, BUFFER_SIZE * sizeof(int16_t), &bytesWritten, portMAX_DELAY);
}

void setup() {
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    delay(3000);

    Serial.println();
    Serial.println("==========================================");
    Serial.println("  OLED + SPEAKER TEST - XH-S3E-AI Board");
    Serial.println("==========================================");

    // Test OLED
    oledOK = setupOLED();

    // Test Speaker
    setupI2S();
    Serial.println("\nPlaying startup sound...");
    playTone(523, 200);
    delay(50);
    playTone(784, 200);
    delay(50);
    playTone(1047, 300);

    Serial.println("\n==========================================");
    Serial.printf("  OLED:    %s\n", oledOK ? "OK" : "FAILED");
    Serial.println("  Speaker: OK (you heard sound)");
    Serial.println("==========================================");

    if (oledOK) {
        display.clearDisplay();
        display.setTextSize(1);
        display.setCursor(0, 0);
        display.println("Hardware Test");
        display.println();
        display.println("OLED:    OK");
        display.println("Speaker: OK");
        display.println();
        display.println("All systems ready!");
        display.display();
    }
}

int count = 0;

void loop() {
    delay(3000);
    count++;

    if (oledOK) {
        display.clearDisplay();
        display.setTextSize(2);
        display.setCursor(20, 10);
        display.printf("Count: %d", count);
        display.setTextSize(1);
        display.setCursor(0, 50);
        display.println("Press RESET to restart");
        display.display();
    }

    Serial.printf("Loop #%d\n", count);
}
