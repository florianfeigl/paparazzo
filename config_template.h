// config_template.h

#ifndef CONFIG_H
#define CONFIG_H

// BIBLIOTHEKEN
#include <AccelStepper.h>

// LAUFEINSTELLUNGEN 
// Anzahl der und Pausen (in ms) zwischen den Durchläufen
const int repeats = {{REPEATS_PLACEHOLDER}};  
const unsigned long pause_ms = {{PAUSE_PLACEHOLDER}};  

// MOTOREN
// AccelStepper-Objekte anlegen (DRIVER-Modus: stepPin, dirPin)
AccelStepper stepper_column(AccelStepper::DRIVER, 12, 13);
AccelStepper stepper_row(AccelStepper::DRIVER, 6, 7);
// Endstufen-Pins (Enable)
const int enable_pin_rows = 11;
const int enable_pin_columns = 5;

// BEWEGUNG
// 1/16 Microstepping @ 200 Steps/Rev => 3200 Steps/Umdrehung
const int steps_per_revolution = 3200;
const long distance_wells_columns = 1.2 * steps_per_revolution;     // Motordistanz zwischen Spalten bei 24-well Platte
const long distance_wells_row = 0.24 * steps_per_revolution; // Motordistanz zwischen Reihen bei 24-well Platte

        // Kommentar: 
        // Die Distanzen zwischen den Wells koennen so dynamisch 
        // in Abhängigkeit ihrer Menge errechnet werden.
        // --> Datenblatt Mikrotitherplatte

// Geschwindigkeit 
const int max_speed = 8000;
const int accel = 3200;

// Konfiguration Mikrotitherplatte
long positions_column[6];
long positions_row[4];

#endif // CONFIG_H
