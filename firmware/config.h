// config_template.h

#ifndef CONFIG_H
#define CONFIG_H

// Pin Konfiguration
#define STEP_PIN_COLUMN 12
#define DIR_PIN_COLUMN 13
#define ENA_PIN_COLUMN 5
#define STEP_PIN_ROW 6
#define DIR_PIN_ROW 7
#define ENA_PIN_ROW 11

// Motorbewegung
#define MAX_SPEED 8000
#define ACCEL 3200
#define STEPS_PER_REV 3200

#define COLUMNS 6
#define ROWS 4

#define RESPONSE_TIMEOUT 3500

// Laufeinstellungen 
#define REPEATS 2
#define PAUSE_MS 5000

#endif // CONFIG_H
