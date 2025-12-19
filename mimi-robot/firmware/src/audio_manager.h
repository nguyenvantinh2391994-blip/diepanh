/**
 * Mimi Robot - Audio Manager
 * Handles microphone input and speaker output using I2S
 */

#ifndef AUDIO_MANAGER_H
#define AUDIO_MANAGER_H

#include <Arduino.h>
#include <driver/i2s.h>
#include "mbedtls/base64.h"
#include "config.h"

typedef void (*VoiceCallback)(const uint8_t* data, size_t length);

class AudioManager {
public:
    AudioManager() : voiceCallback(nullptr), isRecording(false), voiceDetected(false) {}

    bool begin() {
        // Configure I2S for input (microphone)
        i2s_config_t i2s_config_rx = {
            .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
            .sample_rate = AUDIO_SAMPLE_RATE,
            .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
            .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
            .communication_format = I2S_COMM_FORMAT_STAND_I2S,
            .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
            .dma_buf_count = 4,
            .dma_buf_len = AUDIO_BUFFER_SIZE,
            .use_apll = false,
            .tx_desc_auto_clear = false,
            .fixed_mclk = 0
        };

        i2s_pin_config_t pin_config_rx = {
            .bck_io_num = I2S_BCLK_PIN,
            .ws_io_num = I2S_LRCLK_PIN,
            .data_out_num = I2S_PIN_NO_CHANGE,
            .data_in_num = I2S_DIN_PIN
        };

        esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config_rx, 0, NULL);
        if (err != ESP_OK) {
            Serial.printf("[AUDIO] I2S RX install failed: %d\n", err);
            return false;
        }

        err = i2s_set_pin(I2S_NUM_0, &pin_config_rx);
        if (err != ESP_OK) {
            Serial.printf("[AUDIO] I2S RX pin config failed: %d\n", err);
            return false;
        }

        // Configure I2S for output (speaker)
        i2s_config_t i2s_config_tx = {
            .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
            .sample_rate = AUDIO_SAMPLE_RATE,
            .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
            .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
            .communication_format = I2S_COMM_FORMAT_STAND_I2S,
            .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
            .dma_buf_count = 4,
            .dma_buf_len = AUDIO_BUFFER_SIZE,
            .use_apll = false,
            .tx_desc_auto_clear = true,
            .fixed_mclk = 0
        };

        i2s_pin_config_t pin_config_tx = {
            .bck_io_num = I2S_BCLK_PIN,
            .ws_io_num = I2S_LRCLK_PIN,
            .data_out_num = I2S_DOUT_PIN,
            .data_in_num = I2S_PIN_NO_CHANGE
        };

        err = i2s_driver_install(I2S_NUM_1, &i2s_config_tx, 0, NULL);
        if (err != ESP_OK) {
            Serial.printf("[AUDIO] I2S TX install failed: %d\n", err);
            return false;
        }

        err = i2s_set_pin(I2S_NUM_1, &pin_config_tx);
        if (err != ESP_OK) {
            Serial.printf("[AUDIO] I2S TX pin config failed: %d\n", err);
            return false;
        }

        // Allocate buffers in PSRAM if available
        if (psramFound()) {
            audioBuffer = (int16_t*)ps_malloc(AUDIO_BUFFER_SIZE * sizeof(int16_t));
            playbackBuffer = (uint8_t*)ps_malloc(MAX_PLAYBACK_SIZE);
            Serial.println("[AUDIO] Using PSRAM for buffers");
        } else {
            audioBuffer = (int16_t*)malloc(AUDIO_BUFFER_SIZE * sizeof(int16_t));
            playbackBuffer = (uint8_t*)malloc(MAX_PLAYBACK_SIZE);
            Serial.println("[AUDIO] Using internal RAM for buffers");
        }

        if (!audioBuffer || !playbackBuffer) {
            Serial.println("[AUDIO] Buffer allocation failed!");
            return false;
        }

        Serial.println("[AUDIO] Audio system initialized");
        return true;
    }

    void setVoiceCallback(VoiceCallback callback) {
        voiceCallback = callback;
    }

    void update() {
        // Read audio from microphone
        size_t bytesRead = 0;
        esp_err_t err = i2s_read(I2S_NUM_0, audioBuffer, AUDIO_BUFFER_SIZE * sizeof(int16_t),
                                  &bytesRead, pdMS_TO_TICKS(10));

        if (err != ESP_OK || bytesRead == 0) {
            return;
        }

        size_t samplesRead = bytesRead / sizeof(int16_t);

        // Voice Activity Detection
        int32_t sum = 0;
        for (size_t i = 0; i < samplesRead; i++) {
            sum += abs(audioBuffer[i]);
        }
        int32_t average = sum / samplesRead;

        bool wasVoiceDetected = voiceDetected;
        voiceDetected = average > VAD_THRESHOLD;

        if (voiceDetected) {
            lastVoiceTime = millis();

            if (!isRecording) {
                isRecording = true;
                recordingStartTime = millis();
                recordedSize = 0;
                Serial.println("[AUDIO] Voice detected, starting recording");
            }

            // Accumulate audio data
            if (recordedSize + bytesRead < MAX_RECORDING_SIZE) {
                memcpy(recordingBuffer + recordedSize, audioBuffer, bytesRead);
                recordedSize += bytesRead;
            }

            // Send chunks to server
            if (voiceCallback && bytesRead > 0) {
                voiceCallback((uint8_t*)audioBuffer, bytesRead);
            }

        } else if (isRecording) {
            // Check for silence timeout
            if (millis() - lastVoiceTime > VAD_SILENCE_MS) {
                isRecording = false;
                Serial.printf("[AUDIO] Recording stopped, size: %d bytes\n", recordedSize);

                // Send end-of-speech signal
                if (voiceCallback) {
                    uint8_t endSignal[] = {0xFF, 0xFF, 0xFF, 0xFF};
                    voiceCallback(endSignal, 4);
                }
            }
        }
    }

    bool isVoiceDetected() const { return voiceDetected; }
    bool isCurrentlyRecording() const { return isRecording; }

    void playBase64Audio(const char* base64Data) {
        if (!base64Data || strlen(base64Data) == 0) {
            return;
        }

        // Decode base64 using mbedtls
        size_t inputLen = strlen(base64Data);
        size_t outputLen = 0;

        // First call to get required output length
        mbedtls_base64_decode(NULL, 0, &outputLen,
                              (const unsigned char*)base64Data, inputLen);

        if (outputLen > MAX_PLAYBACK_SIZE) {
            Serial.println("[AUDIO] Playback data too large!");
            return;
        }

        size_t actualLen = 0;
        int ret = mbedtls_base64_decode(playbackBuffer, MAX_PLAYBACK_SIZE, &actualLen,
                                        (const unsigned char*)base64Data, inputLen);

        if (ret == 0 && actualLen > 0) {
            playbackSize = actualLen;
            playbackPos = 0;
            playing = true;
            Serial.printf("[AUDIO] Playing %d bytes\n", actualLen);
        }
    }

    void playRawAudio(const uint8_t* data, size_t length) {
        if (length > MAX_PLAYBACK_SIZE) {
            Serial.println("[AUDIO] Playback data too large!");
            return;
        }

        memcpy(playbackBuffer, data, length);
        playbackSize = length;
        playbackPos = 0;
        playing = true;
    }

    bool isPlaying() const { return playing; }

    void stopPlayback() {
        playing = false;
        playbackPos = 0;
    }

    // Call this from a task to handle playback
    void playbackUpdate() {
        if (!playing || playbackPos >= playbackSize) {
            if (playing) {
                playing = false;
                Serial.println("[AUDIO] Playback finished");
            }
            return;
        }

        size_t chunkSize = min((size_t)AUDIO_BUFFER_SIZE, playbackSize - playbackPos);
        size_t bytesWritten = 0;

        esp_err_t err = i2s_write(I2S_NUM_1, playbackBuffer + playbackPos, chunkSize,
                                   &bytesWritten, pdMS_TO_TICKS(100));

        if (err == ESP_OK) {
            playbackPos += bytesWritten;
        }
    }

    void setVolume(uint8_t volume) {
        // Volume 0-100
        currentVolume = constrain(volume, 0, 100);
    }

private:
    static const size_t MAX_RECORDING_SIZE = 32000 * 5;  // ~5 seconds
    static const size_t MAX_PLAYBACK_SIZE = 32000 * 10;  // ~10 seconds

    VoiceCallback voiceCallback;
    int16_t* audioBuffer = nullptr;
    uint8_t* playbackBuffer = nullptr;
    uint8_t recordingBuffer[MAX_RECORDING_SIZE];

    bool isRecording;
    bool voiceDetected;
    bool playing = false;

    size_t recordedSize = 0;
    size_t playbackSize = 0;
    size_t playbackPos = 0;

    unsigned long lastVoiceTime = 0;
    unsigned long recordingStartTime = 0;
    uint8_t currentVolume = 80;
};

#endif // AUDIO_MANAGER_H
