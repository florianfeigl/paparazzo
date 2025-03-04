#!/usr/bin/env python3

# Row/Column-Listen und total_stations
POSITIONS_COLUMN = [1, 2, 3, 4, 5, 6]  # X-Achse
POSITIONS_ROW = ["A", "B", "C", "D"]  # Y-Achse
TOTAL_STATIONS = len(POSITIONS_ROW) * len(POSITIONS_COLUMN)

# Haupt-Variablen
SER = None  # Serielle Verbindung (wird in init_serial() geöffnet)

# DIRECTORIES
RUN_DIR = None  # Aktueller Haupt-Ordner (z. B. /home/pi/images/run_20230224_103456)
CURRENT_PASS_DIR = None  # Aktueller Unterordner (pass_01, pass_02, etc.)
PASS_FOLDER_NAME = None
BASE_DIR = "/home/pi/Paparazzo"
IMAGES_DIR = "/home/pi/Paparazzo/images"  # Hauptbasis für alle Runs
LOGS_DIR = "/home/pi/Paparazzo/logs"
FIRMWARE_DIR = "/home/pi/Paparazzo/firmware"

# RUNS
REPEATS = 0  # GELESEN AUS GUI
PAUSE_MS = 0
MOVE_COUNT = 0  # WIE VIELE STATIONEN IM AKTUELLEN PASS DURCHLAUFEN?
PASS_COUNT = 0
TOTAL_STATIONS = 0

ARDUINO_CLI_PATH = "arduino-cli"  # Pfad zur arduino-cli
FQBN = "arduino:avr:uno"  # Board-Typ
SERIAL_PORT = "/dev/ttyACM0"  # Arduino-Port (z. B. /dev/ttyACM0 für Linux)
BAUD_RATE = 9600  # Muss zum Sketch passen

TEMPLATE_FILE = "/home/pi/Paparazzo/templates/config_template.h"  # Pfad zur config_template.h
CONFIG_FILE = "/home/pi/Paparazzo/firmware/config.h"  # Die generierte config.h

RESPONSE_TIMEOUT = 3500
