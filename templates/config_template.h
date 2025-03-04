// config_template.h

#ifndef CONFIG_H
#define CONFIG_H

// LAUFEINSTELLUNGEN 
// Anzahl der und Pausen (in ms) zwischen den Durchläufen
const int repeats = {{REPEATS_PLACEHOLDER}};  
const unsigned long pause_ms = {{PAUSE_PLACEHOLDER}};  

// Konfiguration Mikrotitherplatte
long positions_column[6];
long positions_row[4];

// Timeout über den Wells
const int response_timeout = 3500;


#endif // CONFIG_H
