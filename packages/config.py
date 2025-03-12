#!/usr/bin/env python3

import os 

# Positionen
POSITIONS_COLUMN = [1, 2, 3, 4, 5, 6]  # X-Achse
POSITIONS_ROW = ["A", "B", "C", "D"]  # Y-Achse
TOTAL_STATIONS = len(POSITIONS_ROW) * len(POSITIONS_COLUMN)

# Verzeichnisse 
BASE_DIR = os.path.join(os.path.expanduser("~"), "Paparazzo")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
FIRMWARE_DIR = os.path.join(BASE_DIR, "firmware")

# Arduino
ARDUINO_CLI_PATH = "arduino-cli"  # Pfad zur arduino-cli
FQBN = "arduino:avr:uno"  # Board-Typ
SERIAL_PORT = "/dev/ttyACM0"  # Arduino-Port (z. B. /dev/ttyACM0 für Linux)
BAUD_RATE = 9600  # Muss zum Sketch passen
TEMPLATE_FILE = os.path.join(BASE_DIR, "templates", "config_template.h")
CONFIG_FILE = os.path.join(FIRMWARE_DIR, "config.h")

RESPONSE_TIMEOUT = 3500
