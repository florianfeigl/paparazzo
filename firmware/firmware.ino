#include "config.h"
#include <AccelStepper.h>

// AccelStepper-Objekte anlegen (DRIVER-Modus: stepPin, dirPin)
AccelStepper stepper_column(AccelStepper::DRIVER, STEP_PIN_COLUMN, DIR_PIN_COLUMN);
AccelStepper stepper_row(AccelStepper::DRIVER, STEP_PIN_ROW, DIR_PIN_ROW);

// Endstufen-Pins (Enable)
const int enable_stepper_rows = ENA_PIN_ROW;
const int enable_stepper_columns = ENA_PIN_COLUMN;

// Bewegungseinstellungen
const int max_speed = MAX_SPEED;
const int accel = ACCEL;

// 1/16 Microstepping @ 200 Steps/Rev => 3200 Steps/Umdrehung
const int steps_base_value = STEPS_BASE_VALUE;
const int microsteps_per_step = MICROSTEPS_PER_STEP;
const int steps_per_revolution = STEPS_BASE_VALUE * MICROSTEPS_PER_STEP;
const long distance_columns = DISTANCE_COLS * steps_per_revolution;
const long distance_rows = DISTANCE_ROWS * steps_per_revolution;

// Startposition als 0 definieren
long positions_column[COLUMNS];
long positions_row[ROWS];

// Timeout über den Wells
const int response_timeout = RESPONSE_TIMEOUT;

// Variablen für Wiederholungen und Pausenzeit (müssen definiert sein!)
const int repeats = REPEATS;
const int pause_ms = PAUSE_MS;

String serialBuffer = "";  // Buffer für serielle Eingaben

void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.flush();

    // Motor-Geschwindigkeiten und Beschleunigung setzen (muss in `setup()` sein)
    stepper_column.setAcceleration(accel);
    stepper_column.setMaxSpeed(max_speed);
    stepper_row.setAcceleration(accel);
    stepper_row.setMaxSpeed(max_speed);

    // Startposition zurücksetzen (aktuelle Position = 0)
    stepper_column.setCurrentPosition(0);
    stepper_row.setCurrentPosition(0);

    // Positionen festlegen
    for (int i = 0; i < 6; i++) {
        positions_column[i] = i * distance_columns;
    }
    for (int i = 0; i < 4; i++) {
        positions_row[i] = i * -distance_rows;
    }

    // Enable-Pins als OUTPUT setzen
    pinMode(enable_stepper_rows, OUTPUT);
    pinMode(enable_stepper_columns, OUTPUT);

    // Motoren deaktivieren (HIGH = disabled)
    //digitalWrite(enable_stepper_rows, HIGH);
    //digitalWrite(enable_stepper_columns, HIGH);

    // Treiber aktivieren (LOW = enabled)
    digitalWrite(enable_stepper_rows, LOW);
    digitalWrite(enable_stepper_columns, LOW);

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
                moveToNextRow(y + 1);
            }
        }
        returnToHome();
        Serial.println("✅ Run finished. Waiting " + String(pause_ms) + " ms for next run.");
        delay(pause_ms);
    }
    sendStatus("DONE");
    Serial.println("✅ ALL runs finished. Cutting polling.");
    while (true) {}
}

void moveToWell(int x, int y) {
    Serial.println("Moving to well " + String(x) + " in column " + String(y));
    stepper_column.runToNewPosition(positions_column[x]);
    sendStatus("MOVE_COMPLETED");
    waitForNextCommand();
}

void moveToNextRow(int y) {
    Serial.println("Moving to next row y: " + String(y));
    stepper_row.runToNewPosition(positions_row[y]);
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
                Serial.println("Start command received. Starting program...");
                break;
            }
        }
    }
}

void waitForNextCommand() {
    unsigned long startTime = millis();
    while (true) {
        if (millis() - startTime > RESPONSE_TIMEOUT) {
            Serial.println("⏳ Timeout: No response from Raspberry Pi. Skipping...");
            break;
        }
        if (Serial.available() > 0) {
            String command = Serial.readStringUntil('\n');
            command.trim();
            command.toUpperCase();

            Serial.print("DEBUG: Empfangener Befehl: ");
            Serial.println(command); // Debugging: Zeige empfangenen Text

            if (command.equals("NEXT_MOVE")) {
                Serial.println("✅ Received 'NEXT_MOVE'. Moving to next position.");
                break;
            } else if (command.equals("ABORT")) {
                handleAbort();
                break;
            }
        }
        delay(10); // CPU entlasten
    }
}

void handleAbort() {
    Serial.println("Aborting operation, returning to home position.");
    returnToHome();
    while (true) {}
}
