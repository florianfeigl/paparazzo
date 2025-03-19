#include "config.h"
#include <AccelStepper.h>

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
        for (int y = 0; y < ROWS; y++) {
            for (int x = 0; x < COLUMNS; x++) {
                moveToWell(x, y); // => <MOVE_COMPLETED>
                waitForNextMoveCommand();
                handleAbort();
            }
            // Auf Startposition zurückfahren
            stepper_column.runToNewPosition(0);

            if (y < ROWS - 1) {
                moveToNextRow(y + 1);
            }
        }
        returnToHome();

        sendStatus("PASS_COMPLETED");
        waitForNextPassCommand();
        handleAbort();

        Serial.println("✅ Run " + String(run + 1) + " finished. Pausing for " + String(PAUSE_MS) + " ms.");
        delay(PAUSE_MS);
    }

    sendStatus("DONE");
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
void moveToWell(int x, int y) {
    Serial.println("➡️ Moving to well [Column: " + String(x) + ", Row: " + String(y) + "]");
    stepper_column.runToNewPosition(positions_column[x]);
    sendStatus("MOVE_COMPLETED");
}

void moveToNextRow(int y) {
    Serial.println("↪️ Moving to next row: " + String(y));
    stepper_row.runToNewPosition(positions_row[y]);
    sendStatus("ROW_COMPLETED");
}

void returnToHome() {
    Serial.println("🏠 Returning to home position...");
    stepper_column.runToNewPosition(0);
    stepper_row.runToNewPosition(0);
    sendStatus("HOME_POSITION");
}

// === Serielle Kommunikationsfunktionen ===

void waitForSpecificCommand(String expectedCommand) {
    serialBuffer = "";
    while (true) {
        if (Serial.available()) {
            serialBuffer = Serial.readStringUntil('\n');
            serialBuffer.trim();

            if (serialBuffer == expectedCommand) {
                Serial.println("✅ " + expectedCommand + " received.");
                break;
            } else {
                Serial.println("❌ Non-functional input: " + serialBuffer);
                serialBuffer = "";
            }
        }
    }
}

void waitForStartCommand() {
    Serial.println("🟢 Waiting for START command...");
    waitForSpecificCommand("START");
    Serial.println("✅ START received, beginning operation...");
}

void waitForSpecificCommandWithTimeout(String expectedCommand, int timeout = 5000) {
    serialBuffer = "";
    unsigned long startMillis = millis();

    while (millis() - startMillis < timeout) {
        if (Serial.available()) {
            serialBuffer = Serial.readStringUntil('\n');
            serialBuffer.trim();

            if (serialBuffer == expectedCommand) {
                Serial.println("✅ " + expectedCommand + " received.");
                return;
            } else {
                Serial.println("❌ Non-functional input: " + serialBuffer);
                serialBuffer = "";  // Zurücksetzen, um falsche Werte zu vermeiden
            }
        }
    }

    Serial.println("⏰ Timeout waiting for command: " + expectedCommand);
}

void waitForNextMoveCommand() {
    Serial.println("Waiting for NEXT_MOVE command...");
    waitForSpecificCommandWithTimeout("NEXT_MOVE", RESPONSE_TIMEOUT);
    Serial.println("✅ NEXT_MOVE received, beginning operation...");
}

void waitForNextPassCommand() {
    Serial.println("Waiting for NEXT_PASS command...");
    waitForSpecificCommandWithTimeout("NEXT_PASS", RESPONSE_TIMEOUT);
    Serial.println("✅ NEXT_PASS received, beginning operation...");
}

//if (command == "END") {
//    stopAllMotors();          // stoppt Motoren/Aktoren
//    resetPositionCounters();  // setzt interne Zähler zurück
//    digitalWrite(LED_BUILTIN, LOW); // Statusanzeige ausschalten
//    Serial.println("<ENDED>"); // Optionale Rückmeldung
//}

void sendStatus(String status) {
    Serial.println("<" + status + ">");
}

// === Notfall-Abbruchfunktion ===
void handleAbort() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        if (command == "ABORT") {
            Serial.println("🛑 ABORT received! Returning motors to 0. Stopping all operations.");
            sendStatus("<ABORTED>");
            stepper_column.runToNewPosition(0);
            stepper_row.runToNewPosition(0);
            while (true);
        }
    }
}
