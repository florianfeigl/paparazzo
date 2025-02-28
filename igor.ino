// ----------------------------------------------------------------------------
// File             : paparazzo.ino
// Author           : Florian Feigl (florian.feigl@stud.plus.ac.at)
// Supervisor       : Prof. Dr. Obermeyer (gerhard.obermeyer@plus.ac.at)
// Modified         : 27.02.2025
// Version          : 0.7
//
// Abstract         :
// This program serves the purpose of moving two stepper motors to scan a two
// dimensional area with cameras.
//
// Libraries        :
// - <AccelStepper.h>
//
// Hardware         :
// - Arduino Uno Rev3
// - Nema 17 Stepper Motors
// - TB6600 Stepper Motor Drivers
// - Raspberry Pi 4 Model B
//
// License/Disclaimer:
// This project is done in context of an academic course and can only be
// used for learning or demonstration purposes.
// ----------------------------------------------------------------------------

#include "config.h"

// FUNKTIONEN
// Hilfsfunktion: Log-Meldung über Hardware-Serial ausgeben
void logMessage(String message, bool newline = true) {
  Serial.print("[");
  Serial.print(millis());
  Serial.print(" ms] ");
  if (newline) {
    Serial.println(message);
  } else {
    Serial.print(message);
  }
}

// Hilfsfunktion: Status an Raspberry Pi senden
void sendStatus(const char* status) {
  // Im Python-Skript suchen wir nach <MOVE_COMPLETED> etc.
  Serial.print("<");
  Serial.print(status);
  Serial.println(">");
  delay(50);
}

void setup() {
  // Hardware-Serial starten (USB-Anschluss zum Pi)
  Serial.begin(9600);
  Serial.flush();

  // Schrittweiten vorbereiten
  for (int i = 0; i < 6; i++) {
    positions_column[i] = i * distance_wells_columns;
  }
  for (int i = 0; i < 4; i++) {
    positions_row[i] = i * -distance_wells_row;
  }

  // Enable-Pins per INPUT_PULLUP deaktivieren (High = disabled)
  pinMode(enable_pin_rows, OUTPUT);
  pinMode(enable_pin_columns, OUTPUT);

  // Optional: Erst mal disabled halten
  digitalWrite(enable_pin_rows, HIGH);
  digitalWrite(enable_pin_columns, HIGH);

  // Dann auf Kommando die Treiber enablen:
  digitalWrite(enable_pin_rows, LOW);
  digitalWrite(enable_pin_columns, LOW);

  // Warten auf das Kommando "START" von Raspberry Pi
  while (true) {
    if (Serial.available() > 0) {
      String command = Serial.readStringUntil('\n');
      command.trim();  // Leerzeichen/Zeilenumbrüche entfernen

      if (command.equals("START")) {
        logMessage("'START' command received. Starting program...");
        break;
      }
    }
  }

  // Geschwindigkeiten und Beschleunigung einstellen
  stepper_column.setMaxSpeed(max_speed);
  stepper_column.setAcceleration(accel);
  stepper_row.setMaxSpeed(max_speed);
  stepper_row.setAcceleration(accel);

  // Startposition als 0 definieren
  stepper_column.setCurrentPosition(0);
  stepper_row.setCurrentPosition(0);
}

void loop() {
  // Hauptschleife, wie oft das Programm gefahren wird
  for (int i = 0; i < repeats; i++) {
    // Geschachtelte Schleifen: y = Spalten (0..3), x = Reihen (0..5)
    for (int y = 0; y < 4; y++) {  
      for (int x = 0; x < 6; x++) {
        // Position in x-Richtung anfahren
        logMessage("Moving to well " + String(x) +
            " (" + String(positions_column[x]) + " steps)" +
            " in column " + String(y) +      
            " (" + String(positions_row[y]) + " steps)");

        stepper_column.runToNewPosition(positions_column[x]);
        logMessage("✅ Movement completed.");

        // An den Raspberry Pi melden, dass wir am Ziel sind
        sendStatus("MOVE_COMPLETED");
        logMessage("Sent 'MOVE_COMPLETED' status.");

        // Auf "NEXT" vom Raspberry Pi warten (max. 4 Sekunden)
        bool waitingForNext = true;
        unsigned long startTime = millis();
        while (waitingForNext) {
          if (millis() - startTime > 4000) {
            logMessage("⏳ Timeout: No response from Raspberry Pi. Skipping...");
            break;
          }
          if (Serial.available() > 0) {
            String command = Serial.readStringUntil('\n');
            command.trim();
            if (command.equals("NEXT")) {
              logMessage("✅ Received 'NEXT'. Moving to next position.");
              waitingForNext = false;
            } else if (command.equals("ABORT")) {
              // ABBRUCHLOGIK
              goto ABORT_LABEL;
            }
          }
        }
      }

      // Am Ende jeder X-Schleife wieder in Ausgangslage auf X=0 fahren
      stepper_column.runToNewPosition(0);

      // In die nächste Y-Position wechseln (außer beim letzten Durchlauf)
      if (y < 3) {
        logMessage("Moving to next column. y: " + String(y+1) +
            " => " + String(positions_column[y + 1]) + " steps");
        stepper_column.runToNewPosition(positions_column[y + 1]);
      }
    }

    // Ganz am Schluss zurück auf Home-Position
    logMessage("🏁 Returning to home position.");
    stepper_column.runToNewPosition(0);
    stepper_row.runToNewPosition(0);

    // Ende
    logMessage("✅ Run finished. Waiting {pause_ms} ms for next run.");

    delay(pause_ms);

  }
  while (true) { }

  ABORT_LABEL:
  // Hier landet das Programm bei 'goto ABORT_LABEL;'
  // => direkt abbrechen & Home-Position
  stepper_column.runToNewPosition(0);
  stepper_row.runToNewPosition(0);
  // Endlosschleife, "Aus"
  while (true) { }
}
