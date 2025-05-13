#include "config.h"
#include <Wire.h>
#include <RTClib.h>
#include <AccelStepper.h>

// === RTC ===
RTC_DS3231 rtc;

// === Funktionsprototypen ===
void waitForNextMoveCommand();
void waitForNextCycleCommand();
void handleTimeout();
void resetSystemState();
void stopAllMotors();
void sendStatus(String status);
String getTimestamp();

// === AccelStepper-Objekte ===
AccelStepper stepper_column(AccelStepper::DRIVER, STEP_PIN_COLUMN, DIR_PIN_COLUMN);
AccelStepper stepper_row(AccelStepper::DRIVER, STEP_PIN_ROW, DIR_PIN_ROW);

// === Pins ===
const int enable_stepper_rows = ENA_PIN_ROW;
const int enable_stepper_columns = ENA_PIN_COLUMN;

// === Bewegungseinstellungen ===
const int steps_per_revolution = STEPS_BASE_VALUE * MICROSTEPS_PER_STEP;
const long distance_columns = DISTANCE_COLS * steps_per_revolution;
const long distance_rows = DISTANCE_ROWS * steps_per_revolution;

// === Positionsspeicher ===
long positions_column[COLUMNS];
long positions_row[ROWS];

// === System Variablen ===
int currentCycle = 0;
int currentRow = 0;
int currentColumn = 0;

// === Serielle Kommunikation ===
String serialBuffer = "";

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.flush();

    if (!rtc.begin()) {
        Serial.println("RTC nicht gefunden!");
        while (1);
    }

    // Bei Erststart/Neusetzung entkommentieren 
    // rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));

    setupSteppers();
    calculatePositions();
    setupPins();

    waitForStartCommand();
}

void loop() {
    for (int run = 0; run < REPEATS; run++) {
        for (int currentRow = 0; currentRow < ROWS; currentRow++) {
            for (int currentColumn = 0; currentColumn < COLUMNS; currentColumn++) {
                moveToNextColumn(currentColumn, currentRow);
                waitForNextMoveCommand();
            }
            stepper_column.runToNewPosition(0);
            if (currentRow < ROWS - 1) {
                moveToNextRow(currentRow + 1);
            }
        }
        returnToHome();
        waitForNextCycleCommand();

        Serial.println("✅ Cycle " + String(run + 1) + " finished at " + getTimestamp() + ". Pausing for " + String(PAUSE_MS) + " ms.");
        delay(PAUSE_MS);
    }
    Serial.println("✅ ALL cycles completed at " + getTimestamp() + ". Run completed. Halting execution.");
    while (true);
}

void setupSteppers() {
    stepper_column.setAcceleration(ACCEL);
    stepper_column.setMaxSpeed(MAX_SPEED);
    stepper_row.setAcceleration(ACCEL);
    stepper_row.setMaxSpeed(MAX_SPEED);

    stepper_column.setCurrentPosition(0);
    stepper_row.setCurrentPosition(0);
}

void calculatePositions() {
    for (int i = 0; i < COLUMNS; i++) {
        positions_column[i] = i * distance_columns;
    }
    for (int i = 0; i < ROWS; i++) {
        positions_row[i] = i * -distance_rows;
    }
}

void setupPins() {
    pinMode(enable_stepper_rows, OUTPUT);
    pinMode(enable_stepper_columns, OUTPUT);

    digitalWrite(enable_stepper_rows, LOW);
    digitalWrite(enable_stepper_columns, LOW);
}

void moveToNextColumn(int currentColumn, int currentRow) {
    Serial.println("Moving to column: " + String(currentColumn) + "/" + String(currentRow));
    stepper_column.runToNewPosition(positions_column[currentColumn]);
    sendStatus("MOVE_COMPLETED");
}

void moveToNextRow(int currentRow) {
    Serial.println("Moving to row: " + String(currentRow));
    stepper_row.runToNewPosition(positions_row[currentRow]);
    sendStatus("ROW_COMPLETED");
}

void returnToHome() {
    Serial.println("🏠 Returning to home position...");
    stepper_column.runToNewPosition(0);
    stepper_row.runToNewPosition(0);
    sendStatus("HOME_POSITION");
}

void waitForStartCommand() {
    serialBuffer = "";
    while (true) {
        if (Serial.available()) {
            serialBuffer = Serial.readStringUntil('\n');
            serialBuffer.trim();

            if (serialBuffer == "START") {
                Serial.println("✅ Command 'START' received at " + getTimestamp() + ".");
                break;
            } else {
                Serial.println("❌ Non-functional input: " + serialBuffer);
                serialBuffer = "";
            }
        }
    }
}

void waitForNextMoveCommand() {
    serialBuffer = "";
    unsigned long startMillis = millis();

    while (millis() - startMillis < RESPONSE_TIMEOUT) {
        if (Serial.available()) {
            serialBuffer = Serial.readStringUntil('\n');
            serialBuffer.trim();

            if (serialBuffer == "NEXT_MOVE") {
                Serial.println("✅ Command NEXT_MOVE received at " + getTimestamp() + ".");
                return;
            } else if (serialBuffer == "ABORT") {
                Serial.println("🛑 ABORT received at " + getTimestamp() + ". Shutting down.");
                returnToHome();
                stopAllMotors();
                resetSystemState();
                sendStatus("ABORTED");
                return;
            } else {
                Serial.println("❌ Non-functional input: " + serialBuffer);
                serialBuffer = "";
                handleTimeout();
            }
        }
    }
}

void waitForNextCycleCommand() {
    sendStatus("CYCLE_COMPLETED");

    serialBuffer = "";
    unsigned long startMillis = millis();

    while (millis() - startMillis < RESPONSE_TIMEOUT) {
        if (Serial.available()) {
            serialBuffer = Serial.readStringUntil('\n');
            serialBuffer.trim();

            if (serialBuffer == "NEXT_CYCLE") {
                Serial.println("✅ Command 'NEXT_CYCLE' received at " + getTimestamp() + ".");
                return;
            } else if (serialBuffer == "ABORT") {
                Serial.println("🛑 ABORT received at " + getTimestamp() + ". Shutting down.");
                returnToHome();
                stopAllMotors();
                resetSystemState();
                sendStatus("ABORTED");
                return;
            } else if (serialBuffer == "END") {
                stopAllMotors();
                resetSystemState();
                sendStatus("ENDED");
                return;
            } else {
                Serial.println("❌ Non-functional input: " + serialBuffer);
                serialBuffer = "";
                handleTimeout();
            }
        }
    }
}

void resetSystemState() {
    currentRow = 0;
    currentColumn = 0;
    currentCycle = 0;
    Serial.println("✅ Systemzustand zurückgesetzt bei " + getTimestamp() + ".");
}

void stopAllMotors() {
    stepper_column.stop();
    stepper_row.stop();
    digitalWrite(enable_stepper_rows, HIGH);
    digitalWrite(enable_stepper_columns, HIGH);
}

void handleTimeout() {
    Serial.println("⏰ TIMEOUT at " + getTimestamp() + "! Returning motors to home position and resetting system state.");
    returnToHome();
    stopAllMotors();
    resetSystemState();
    sendStatus("TIMEOUT");
    return;
}

void sendStatus(String status) {
    Serial.println("<" + status + ">");
}

String getTimestamp() {
    DateTime now = rtc.now();
    char timestamp[20];
    sprintf(timestamp, "%04d-%02d-%02d_%02d-%02d-%02d",
            now.year(), now.month(), now.day(),
            now.hour(), now.minute(), now.second());
    return String(timestamp);
}
