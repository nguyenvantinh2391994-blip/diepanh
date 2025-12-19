/**
 * Mimi Robot - Display Manager
 * Handles OLED display with cute face expressions
 */

#ifndef DISPLAY_MANAGER_H
#define DISPLAY_MANAGER_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

class DisplayManager {
public:
    enum Face {
        HAPPY,
        SAD,
        LISTENING,
        THINKING,
        TALKING,
        SLEEPING,
        SURPRISED,
        LOVE,
        WINK
    };

    DisplayManager() : display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1) {}

    bool begin() {
        Serial.println("[DISPLAY] Initializing I2C...");
        Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);

        // CRITICAL: Wait for I2C bus and OLED power to stabilize after power cycle
        delay(150);

        // Try to recover I2C bus if stuck from previous session
        Wire.beginTransmission(OLED_ADDR);
        Wire.endTransmission();
        delay(10);

        Serial.println("[DISPLAY] Initializing SSD1306...");

        // Try multiple times in case of power instability
        for (int attempt = 0; attempt < 3; attempt++) {
            if (display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
                Serial.println("[DISPLAY] SSD1306 initialized successfully!");
                break;
            }
            Serial.printf("[DISPLAY] Attempt %d failed, retrying...\n", attempt + 1);
            delay(100);
            if (attempt == 2) {
                Serial.println("[DISPLAY] SSD1306 init failed after 3 attempts!");
                return false;
            }
        }

        display.clearDisplay();
        display.setTextColor(SSD1306_WHITE);
        display.setTextSize(1);
        display.display();

        return true;
    }

    void showBootScreen() {
        display.clearDisplay();
        display.setTextSize(2);
        display.setCursor(30, 10);
        display.println("Mimi");
        display.setTextSize(1);
        display.setCursor(20, 35);
        display.println("Starting up...");
        display.display();
    }

    void showStatus(const char* status) {
        display.clearDisplay();
        display.setTextSize(1);
        display.setCursor(0, 28);
        display.println(status);
        display.display();
    }

    void showError(const char* error) {
        display.clearDisplay();
        display.setTextSize(1);
        display.setCursor(0, 0);
        display.println("Error:");
        display.setCursor(0, 15);
        display.println(error);
        display.display();
    }

    void showText(const char* text) {
        display.clearDisplay();
        display.setTextSize(1);
        display.setCursor(0, 0);
        display.println(text);
        display.display();
    }

    void showFace(Face face) {
        currentFace = face;
        display.clearDisplay();

        switch (face) {
            case HAPPY:
                drawHappyFace();
                break;
            case SAD:
                drawSadFace();
                break;
            case LISTENING:
                drawListeningFace();
                break;
            case THINKING:
                drawThinkingFace();
                break;
            case TALKING:
                drawTalkingFace();
                break;
            case SLEEPING:
                drawSleepingFace();
                break;
            case SURPRISED:
                drawSurprisedFace();
                break;
            case LOVE:
                drawLoveFace();
                break;
            case WINK:
                drawWinkFace();
                break;
        }

        display.display();
    }

    void showFaceByName(const char* name) {
        if (strcmp(name, "happy") == 0) showFace(HAPPY);
        else if (strcmp(name, "sad") == 0) showFace(SAD);
        else if (strcmp(name, "listening") == 0) showFace(LISTENING);
        else if (strcmp(name, "thinking") == 0) showFace(THINKING);
        else if (strcmp(name, "talking") == 0) showFace(TALKING);
        else if (strcmp(name, "sleeping") == 0) showFace(SLEEPING);
        else if (strcmp(name, "surprised") == 0) showFace(SURPRISED);
        else if (strcmp(name, "love") == 0) showFace(LOVE);
        else if (strcmp(name, "wink") == 0) showFace(WINK);
    }

    void update() {
        // Animation updates
        if (currentFace == THINKING) {
            animateThinking();
        } else if (currentFace == TALKING) {
            animateTalking();
        } else if (currentFace == LISTENING) {
            animateListening();
        }
    }

private:
    Adafruit_SSD1306 display;
    Face currentFace = HAPPY;
    unsigned long lastAnimFrame = 0;
    int animFrame = 0;

    // Eye positions
    const int leftEyeX = 40;
    const int rightEyeX = 88;
    const int eyeY = 25;
    const int eyeRadius = 12;

    // Drawing helper functions
    void drawHappyFace() {
        // Eyes - happy curved
        display.fillCircle(leftEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        display.fillCircle(rightEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        // Eye highlights
        display.fillCircle(leftEyeX - 3, eyeY - 3, 3, SSD1306_BLACK);
        display.fillCircle(rightEyeX - 3, eyeY - 3, 3, SSD1306_BLACK);
        // Smile
        drawSmile(64, 48, 20, true);
    }

    void drawSadFace() {
        // Sad eyes
        display.fillCircle(leftEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        display.fillCircle(rightEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        // Sad eyebrows
        display.drawLine(leftEyeX - 10, eyeY - 15, leftEyeX + 5, eyeY - 12, SSD1306_WHITE);
        display.drawLine(rightEyeX - 5, eyeY - 12, rightEyeX + 10, eyeY - 15, SSD1306_WHITE);
        // Sad mouth
        drawSmile(64, 48, 15, false);
    }

    void drawListeningFace() {
        // Wide open eyes
        display.fillCircle(leftEyeX, eyeY, eyeRadius + 2, SSD1306_WHITE);
        display.fillCircle(rightEyeX, eyeY, eyeRadius + 2, SSD1306_WHITE);
        display.fillCircle(leftEyeX, eyeY, 5, SSD1306_BLACK);
        display.fillCircle(rightEyeX, eyeY, 5, SSD1306_BLACK);
        // Small open mouth
        display.fillCircle(64, 50, 5, SSD1306_WHITE);
    }

    void drawThinkingFace() {
        // Looking up/side eyes
        display.fillCircle(leftEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        display.fillCircle(rightEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        display.fillCircle(leftEyeX + 4, eyeY - 4, 4, SSD1306_BLACK);
        display.fillCircle(rightEyeX + 4, eyeY - 4, 4, SSD1306_BLACK);
        // Thinking dots
        display.fillCircle(100, 20, 2, SSD1306_WHITE);
        display.fillCircle(108, 15, 3, SSD1306_WHITE);
        display.fillCircle(118, 10, 4, SSD1306_WHITE);
        // Neutral mouth
        display.drawLine(54, 50, 74, 50, SSD1306_WHITE);
    }

    void drawTalkingFace() {
        // Normal eyes
        display.fillCircle(leftEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        display.fillCircle(rightEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        display.fillCircle(leftEyeX, eyeY, 4, SSD1306_BLACK);
        display.fillCircle(rightEyeX, eyeY, 4, SSD1306_BLACK);
        // Open mouth (animated)
        int mouthHeight = 5 + (animFrame % 3) * 3;
        display.fillRoundRect(54, 45, 20, mouthHeight, 3, SSD1306_WHITE);
    }

    void drawSleepingFace() {
        // Closed eyes (lines)
        display.drawLine(leftEyeX - 10, eyeY, leftEyeX + 10, eyeY, SSD1306_WHITE);
        display.drawLine(rightEyeX - 10, eyeY, rightEyeX + 10, eyeY, SSD1306_WHITE);
        // Zzz
        display.setTextSize(1);
        display.setCursor(100, 10);
        display.print("Z");
        display.setCursor(108, 5);
        display.print("z");
        display.setCursor(115, 0);
        display.print("z");
    }

    void drawSurprisedFace() {
        // Big round eyes
        display.fillCircle(leftEyeX, eyeY, eyeRadius + 3, SSD1306_WHITE);
        display.fillCircle(rightEyeX, eyeY, eyeRadius + 3, SSD1306_WHITE);
        display.fillCircle(leftEyeX, eyeY, 6, SSD1306_BLACK);
        display.fillCircle(rightEyeX, eyeY, 6, SSD1306_BLACK);
        // O mouth
        display.drawCircle(64, 50, 8, SSD1306_WHITE);
    }

    void drawLoveFace() {
        // Heart eyes
        drawHeart(leftEyeX, eyeY, 12);
        drawHeart(rightEyeX, eyeY, 12);
        // Happy smile
        drawSmile(64, 48, 18, true);
    }

    void drawWinkFace() {
        // Left eye open
        display.fillCircle(leftEyeX, eyeY, eyeRadius, SSD1306_WHITE);
        display.fillCircle(leftEyeX, eyeY, 4, SSD1306_BLACK);
        // Right eye winking (arc)
        display.drawLine(rightEyeX - 10, eyeY, rightEyeX + 10, eyeY, SSD1306_WHITE);
        display.drawLine(rightEyeX + 10, eyeY, rightEyeX + 5, eyeY - 5, SSD1306_WHITE);
        // Smile
        drawSmile(64, 48, 18, true);
    }

    void drawSmile(int x, int y, int width, bool happy) {
        if (happy) {
            // Happy smile (arc going down)
            for (int i = -width; i <= width; i++) {
                int yOffset = (i * i) / (width * 2);
                display.drawPixel(x + i, y + yOffset, SSD1306_WHITE);
                display.drawPixel(x + i, y + yOffset + 1, SSD1306_WHITE);
            }
        } else {
            // Sad frown (arc going up)
            for (int i = -width; i <= width; i++) {
                int yOffset = (i * i) / (width * 2);
                display.drawPixel(x + i, y + 5 - yOffset, SSD1306_WHITE);
                display.drawPixel(x + i, y + 6 - yOffset, SSD1306_WHITE);
            }
        }
    }

    void drawHeart(int x, int y, int size) {
        // Simple heart shape
        display.fillCircle(x - size/3, y - size/4, size/3, SSD1306_WHITE);
        display.fillCircle(x + size/3, y - size/4, size/3, SSD1306_WHITE);
        display.fillTriangle(
            x - size/2 - 2, y,
            x + size/2 + 2, y,
            x, y + size/2 + 2,
            SSD1306_WHITE
        );
    }

    void animateThinking() {
        if (millis() - lastAnimFrame > 500) {
            lastAnimFrame = millis();
            animFrame = (animFrame + 1) % 3;
            showFace(THINKING);
        }
    }

    void animateTalking() {
        if (millis() - lastAnimFrame > 150) {
            lastAnimFrame = millis();
            animFrame = (animFrame + 1) % 4;
            showFace(TALKING);
        }
    }

    void animateListening() {
        if (millis() - lastAnimFrame > 300) {
            lastAnimFrame = millis();
            animFrame = (animFrame + 1) % 2;
            // Pulse effect
            showFace(LISTENING);
        }
    }
};

#endif // DISPLAY_MANAGER_H
