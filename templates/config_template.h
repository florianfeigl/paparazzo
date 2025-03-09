// config_template.h

#ifndef CONFIG_H
#define CONFIG_H

// Serielle Parameter
#define SERIAL_BAUD 9600

// Pin Konfiguration
#define STEP_PIN_COLUMN 12
#define DIR_PIN_COLUMN 13
#define ENA_PIN_COLUMN 5
#define STEP_PIN_ROW 6
#define DIR_PIN_ROW 7
#define ENA_PIN_ROW 11

// Motoreinstellungen 
#define MAX_SPEED 8000
#define ACCEL 3200
#define STEPS_BASE_VALUE 200
#define MICROSTEPS_PER_STEP 16
#define DISTANCE_COLS 1.2
#define DISTANCE_ROWS 0.24

// Brunnenplatte
#define COLUMNS 6
#define ROWS 4

// Laufeinstellungen
#define REPEATS {{REPEATS_PLACEHOLDER}}
#define PAUSE_MS {{PAUSE_PLACEHOLDER}}
#define RESPONSE_TIMEOUT 5000 

#endif // CONFIG_H
