# KONFIGURATION

ARDUINO_CLI_PATH = "arduino-cli"  # Pfad zur arduino-cli
FQBN = "arduino:avr:uno"  # Board-Typ
SERIAL_PORT = "/dev/ttyACM0"  # Arduino-Port (z. B. /dev/ttyACM0 für Linux)
BAUD_RATE = 9600  # Muss zum Sketch passen

TEMPLATE_FILE = "config_template.h"  # Pfad zur config_template.h
CONFIG_FILE = "config.h"  # Die generierte config.h

BASE_OUTPUT_DIR = "/home/pi/images"  # Hauptbasis für alle Runs
