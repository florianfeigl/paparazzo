#include "config.h"
#include <AccelStepper.h>

// === Funktionsprototypen ===
void waitForNextMoveCommand();
void waitForNextPassCommand();
void handleTimeout();
void resetSystemState();
void stopAllMotors();
void sendStatus(String status);

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
int currentPass = 0;
int currentRow = 0;
int currentColumn = 0;

// === Serielle Kommunikation ===
String serialBuffer = "";

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.flush();

    setupSteppers();
    calculatePositions();
    setupPins();

    waitForStartCommand();
}

void loop() {
    for (int run = 0; run < REPEATS; run++) {
        for (int currentRow = 0; currentRow < ROWS; currentRow++) {
            for (int currentColumn = 0; currentColumn < COLUMNS; currentColumn++) {
                // Reihe entlang der Spalten fahren
                moveToNextColumn(currentColumn, currentRow); // => <MOVE_COMPLETED>
                waitForNextMoveCommand();
            }
            // 
            stepper_column.runToNewPosition(0);
            if (currentRow < ROWS - 1) {
                moveToNextRow(currentRow + 1);
            }
        }
        returnToHome();
        waitForNextPassCommand();

        Serial.println("✅ Run " + String(run + 1) + " finished. Pausing for " + String(PAUSE_MS) + " ms.");
        delay(PAUSE_MS);
    }
    Serial.println("✅ ALL runs completed. Halting execution.");
    while (true);
}

// === Initialisierungsfunktionen ===
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

// === Bewegungsfunktionen ===
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

// === Serielle Kommunikationsfunktionen ===
void waitForStartCommand() {
    serialBuffer = "";
    while (true) {
        if (Serial.available()) {
            serialBuffer = Serial.readStringUntil('\n');
            serialBuffer.trim();

            if (serialBuffer == "START") {
                Serial.println("✅ Command 'START' received.");
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
                Serial.println("✅ Command NEXT_MOVE received.");
                return;  
            } else if (serialBuffer == "ABORT") {
                Serial.println("🛑 ABORT received! Shutting down.");
                returnToHome();
                stopAllMotors();
                resetSystemState();
                sendStatus("ABORTED");
                return;
            } else {
                Serial.println("❌ Non-functional input: " + serialBuffer);
                serialBuffer = "";  // Zurücksetzen, um falsche Werte zu vermeiden
                handleTimeout();
            }
        }
    }
}

void waitForNextPassCommand() {
    sendStatus("PASS_COMPLETED");

    serialBuffer = "";
    unsigned long startMillis = millis();

    while (millis() - startMillis < RESPONSE_TIMEOUT) {
        if (Serial.available()) {
            serialBuffer = Serial.readStringUntil('\n');
            serialBuffer.trim();

            if (serialBuffer == "NEXT_PASS") {
                Serial.println("✅ Command 'NEXT_PASS' received.");
                return;  
            } else if (serialBuffer == "ABORT") {
                Serial.println("🛑 ABORT received! Shutting down.");
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
                serialBuffer = "";  // Zurücksetzen, um falsche Werte zu vermeiden
                handleTimeout();
            }
        }
    }
}

// === Helper ===
void resetSystemState() {
    currentRow = 0;
    currentColumn = 0;
    currentPass = 0;
    Serial.println("✅ Systemzustand zurückgesetzt.");
}

void stopAllMotors() {
    stepper_column.stop();
    stepper_row.stop();
    digitalWrite(enable_stepper_rows, HIGH);
    digitalWrite(enable_stepper_columns, HIGH);
}

void handleTimeout() {
    Serial.println("⏰ TIMEOUT! Returning motors to home position and resetting system state.");
    returnToHome();
    stopAllMotors();
    resetSystemState();
    sendStatus("TIMEOUT");
    return;
}
void sendStatus(String status) {
    Serial.println("<" + status + ">");
}
