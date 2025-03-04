#include "config.h"
#include <AccelStepper.h>

// AccelStepper-Objekte anlegen (DRIVER-Modus: stepPin, dirPin)
AccelStepper stepper_column(AccelStepper::DRIVER, 12, 13);
AccelStepper stepper_row(AccelStepper::DRIVER, 6, 7);

// Endstufen-Pins (Enable)
const int enable_row_stepper = 11;
const int enable_column_stepper = 5;

// 1/16 Microstepping @ 200 Steps/Rev => 3200 Steps/Umdrehung
const int steps_per_revolution = 3200;
const long distance_columns = 1.2 * steps_per_revolution;     // Motordistanz zwischen Spalten bei 24-well Platte
const long distance_rows = 0.24 * steps_per_revolution; // Motordistanz zwischen Reihen bei 24-well Platte

// Geschwindigkeiten und Beschleunigung einstellen
const int max_speed = 8000;
const int accel = 3200;

stepper_column.setMaxSpeed(max_speed);
stepper_column.setAcceleration(accel);
stepper_row.setMaxSpeed(max_speed);
stepper_row.setAcceleration(accel);

// Startposition als 0 definieren
stepper_column.setCurrentPosition(0);
stepper_row.setCurrentPosition(0);

String serialBuffer = "";  // Buffer für serielle Eingaben

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.flush();

    // Schrittweiten vorbereiten
    for (int i = 0; i < 6; i++) {
        positions_column[i] = i * distance_columns;
    }
    for (int i = 0; i < 4; i++) {
        positions_row[i] = i * -distance_rows;
    }

    pinMode(ENABLE_PIN, OUTPUT);
    digitalWrite(ENABLE_PIN, LOW);

    waitForStartCommand();
}

void loop() {
    for (int i = 0; i < repeats; i++) {
        for (int y = 0; y < 4; y++) {  
            for (int x = 0; x < 6; x++) {
                moveToWell(x, y);
            }
            stepper_column.runToNewPosition(0);
            if (y < 3) {
                moveToNextColumn(y + 1);
            }
        }
        returnToHome();
        Serial.println("✅ Run finished. Waiting " + String(pause_ms) + " ms for next run.");
        delay(PAUSE_MS);
    }
    while (true) {}
}

void moveToWell(int x, int y) {
    Serial.println("Moving to well " + String(x) + " in column " + String(y));
    stepper_column.runToNewPosition(positions_column[x]);
    sendStatus("MOVE_COMPLETED");
    waitForNextCommand();
}

void moveToNextColumn(int y) {
    Serial.println("Moving to next column y: " + String(y));
    stepper_column.runToNewPosition(positions_column[y]);
}

void returnToHome() {
    Serial.println("🏁 Returning to home position.");
    stepper_column.runToNewPosition(0);
    stepper_row.runToNewPosition(0);
}

void sendStatus(const char* status) {
    Serial.print("<");
    Serial.print(status);
    Serial.println(">");
    delay(50);
}

void waitForStartCommand() {
    while (true) {
        if (Serial.available() > 0) {
            String command = Serial.readStringUntil('\n');
            command.trim();
            if (command.equals("START")) {
                Serial.println("[INFO] Start command received. Starting program...");
                break;
            }
        }
    }
}

void waitForNextCommand() {
    unsigned long startTime = millis();
    while (true) {
        if (millis() - startTime > response_timeout) {
            Serial.println("⏳ Timeout: No response from Raspberry Pi. Skipping...");
            break;
        }
        if (Serial.available() > 0) {
            String command = Serial.readStringUntil('\n');
            command.trim();
            if (command.equals("NEXT")) {
                Serial.println("✅ Received 'NEXT'. Moving to next position.");
                break;
            } else if (command.equals("ABORT")) {
                handleAbort();
                break;
            }
        }
    }
}

void handleAbort() {
    Serial.println("[ERROR] Aborting operation, returning to home position.");
    returnToHome();
    while (true) {}
}
