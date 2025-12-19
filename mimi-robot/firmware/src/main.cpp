/**
 * Speaker Test for XH-S3E-AI Board
 * Tests NS4168 audio amplifier with I2S
 */

#include <Arduino.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include <driver/i2s.h>
#include <math.h>

// I2S pins for NS4168 amplifier (XH-S3E-AI board - from Keyestudio docs)
#define I2S_BCLK    15  // Bit Clock
#define I2S_LRCLK   16  // Left/Right Clock (Word Select)
#define I2S_DOUT    7   // Data Out to speaker

#define SAMPLE_RATE 16000
#define BUFFER_SIZE 1024

int16_t audioBuffer[BUFFER_SIZE];

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
        Serial.printf("I2S driver install failed: %d\n", err);
        return;
    }

    err = i2s_set_pin(I2S_NUM_0, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("I2S set pin failed: %d\n", err);
        return;
    }

    Serial.println("I2S initialized successfully!");
}

// Generate a tone at given frequency
void playTone(int frequency, int durationMs) {
    int samples = (SAMPLE_RATE * durationMs) / 1000;
    float amplitude = 30000;  // Volume MAX (0-32767)

    Serial.printf("Playing %dHz tone for %dms...\n", frequency, durationMs);

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

    // Small silence after tone
    memset(audioBuffer, 0, sizeof(audioBuffer));
    size_t bytesWritten;
    i2s_write(I2S_NUM_0, audioBuffer, BUFFER_SIZE * sizeof(int16_t), &bytesWritten, portMAX_DELAY);
}

void playMelody() {
    Serial.println("\n♪ Playing melody...");

    // Simple melody: C-E-G-C (higher)
    playTone(523, 300);  // C5
    delay(50);
    playTone(659, 300);  // E5
    delay(50);
    playTone(784, 300);  // G5
    delay(50);
    playTone(1047, 500); // C6

    Serial.println("Melody finished!");
}

void setup() {
    WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

    Serial.begin(115200);
    delay(3000);

    Serial.println();
    Serial.println("==========================================");
    Serial.println("  SPEAKER TEST - XH-S3E-AI Board");
    Serial.println("==========================================");
    Serial.printf("BCLK:  GPIO %d\n", I2S_BCLK);
    Serial.printf("LRCLK: GPIO %d\n", I2S_LRCLK);
    Serial.printf("DOUT:  GPIO %d\n", I2S_DOUT);
    Serial.println();

    setupI2S();

    Serial.println("\nPlaying test tones...");
    Serial.println("If speaker is connected, you should hear sounds!\n");

    // Play startup sound
    playMelody();

    Serial.println("\n==========================================");
    Serial.println("  Test complete!");
    Serial.println("  Did you hear the melody?");
    Serial.println("==========================================");
}

int count = 0;

void loop() {
    delay(5000);
    count++;
    Serial.printf("\nPlaying beep #%d...\n", count);
    playTone(1000, 200);  // 1kHz beep
}
