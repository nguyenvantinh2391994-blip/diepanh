/**
 * Mimi Robot - State Machine
 */

#ifndef MIMI_STATE_H
#define MIMI_STATE_H

#include <Arduino.h>

class MimiState {
public:
    enum State {
        IDLE,       // Waiting for input
        LISTENING,  // Recording voice
        THINKING,   // Processing with AI
        SPEAKING,   // Playing response
        ERROR       // Error state
    };

    MimiState() : currentState(IDLE), previousState(IDLE) {}

    void setState(State newState) {
        if (newState != currentState) {
            previousState = currentState;
            currentState = newState;
            stateChangedAt = millis();

            Serial.printf("[STATE] %s -> %s\n",
                stateToString(previousState),
                stateToString(currentState));
        }
    }

    State getState() const { return currentState; }
    State getPreviousState() const { return previousState; }

    unsigned long getStateTime() const {
        return millis() - stateChangedAt;
    }

    bool isState(State state) const {
        return currentState == state;
    }

    static const char* stateToString(State state) {
        switch (state) {
            case IDLE:      return "IDLE";
            case LISTENING: return "LISTENING";
            case THINKING:  return "THINKING";
            case SPEAKING:  return "SPEAKING";
            case ERROR:     return "ERROR";
            default:        return "UNKNOWN";
        }
    }

private:
    State currentState;
    State previousState;
    unsigned long stateChangedAt = 0;
};

#endif // MIMI_STATE_H
