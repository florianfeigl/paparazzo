#!/usr/bin/env python3

import os
import time

import serial

from .config import (BASE_OUTPUT_DIR, BAUD_RATE, CURRENT_PASS_DIR, PASS_FOLDER_NAME,
                     POSITIONS_COLUMN, POSITIONS_ROW, SERIAL_PORT, SER, MOVE_COUNT, TOTAL_STATIONS, PASS_COUNT, REPEATS)
from .logger import log_message, setup_logging

logger = setup_logging()
picam = None

def init_serial():
    """Öffnet den seriellen Port, wenn noch nicht geschehen."""
    global SER
    if SER is None:
        try:
            SER = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            time.sleep(2)  # Arduino-Reset abwarten
            log_message(f"Serieller Port {SERIAL_PORT} geöffnet.")
        except serial.SerialException as e:
            log_message(f"ERROR: Could not open serial port: {e}", level="error")


def send_message(message):
    """Sendet ein Kommando an den Arduino (z. B. 'START', 'NEXT', 'ABORT')."""
    init_serial()
    if SER and SER.is_open:
        SER.write((message + "\n").encode("utf-8"))
        SER.flush()
        log_message(f"=> Arduino: {message}")

# SERIELLE VERBINDUNG AUSLESEN
def read_arduino_line():
    """Liest eine Zeile aus der seriellen Verbindung."""
    init_serial()
    if not (SER and SER.is_open):
        return None

    raw_line = SER.readline().decode("utf-8", errors="ignore").strip()
    if raw_line.startswith("<") and raw_line.endswith(">"):
        return raw_line[1:-1]
    return raw_line


# PHOTO SCHIESSEN & FORTFAHREN
def take_photo_for_pass():
    """Speichert ein Foto mit entsprechender Position."""
    global CURRENT_PASS_DIR, BASE_OUTPUT_DIR, PASS_FOLDER_NAME
    if not picam:
        log_message("Kamera nicht vorhanden.", level="error")
        return

    COL_INDEX = MOVE_COUNT % len(POSITIONS_COLUMN)
    ROW_INDEX = MOVE_COUNT // len(POSITIONS_COLUMN)
    COL_VALUE = POSITIONS_COLUMN[COL_INDEX]
    ROW_VALUE = POSITIONS_ROW[ROW_INDEX]

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"well_{ROW_VALUE}{COL_VALUE}_pass{PASS_COUNT}_{timestamp}.jpg"

    if CURRENT_PASS_DIR is None:
        if BASE_OUTPUT_DIR is None:
            BASE_OUTPUT_DIR = "images"  # Standardverzeichnis setzen, falls nicht vorhanden

        if PASS_FOLDER_NAME is None:
            PASS_FOLDER_NAME = "pass_default"  # Standard-Passname setzen

        CURRENT_PASS_DIR = os.path.join(BASE_OUTPUT_DIR, PASS_FOLDER_NAME)
        os.makedirs(CURRENT_PASS_DIR, exist_ok=True)

    filepath = os.path.join(CURRENT_PASS_DIR, filename)

    try:
        picam.capture_file(filepath)
        log_message(f"Foto aufgenommen: {filepath}")
    except Exception as e:
        log_message(f"Fehler bei Fotoaufnahme: {e}", level="error")


def poll_arduino(self):
    """Liest Arduino-Antworten und verarbeitet sie."""
    global MOVE_COUNT, PASS_COUNT, REPEATS, TOTAL_STATIONS
    line = read_arduino_line()
    if line:
        log_message(f"Arduino: {line}")
        if line == "MOVE_COMPLETED":
            take_photo_for_pass()
            MOVE_COUNT += 1

            if MOVE_COUNT < TOTAL_STATIONS:
                send_message("NEXT")
            else:
                log_message(f"Pass {PASS_COUNT} abgeschlossen.")
                if PASS_COUNT < REPEATS:
                    start_next_pass(self)
                else:
                    log_message("ALLE Wiederholungen abgeschlossen!")


def start_pass_folder(self):
    """Legt den Unterordner (pass_01, pass_02, ...) für den aktuellen Pass an."""
    # Falls self.run_dir noch nicht gesetzt ist, verwende BASE_OUTPUT_DIR als Fallback
    base_dir = self.run_dir if self.run_dir is not None else BASE_OUTPUT_DIR
    pass_folder_name = f"pass_{self.pass_count:02d}"
    self.current_pass_dir = os.path.join(base_dir, pass_folder_name)
    os.makedirs(self.current_pass_dir, exist_ok=True)
    self.log_message(f"Neuer Pass-Ordner angelegt: {self.current_pass_dir}")
    self.move_count = 0


def start_next_pass(self):
    """
    Aufruf, wenn ein Pass beendet ist
    und wir noch weitere Wiederholungen haben.
    """
    self.pass_count += 1
    if self.pass_count <= self.repeats:
        self.start_pass_folder()
        self.send_message("START")
    else:
        self.log_message("Alle Wiederholungen sind erledigt.")


# MANUELLES NEXT
def on_manual_next():
    """
    Button-Callback: Sendet 'NEXT' manuell an den Arduino,
    damit er eine Station weiterfährt.
    """
    log_message("Sende 'NEXT' (manuell).")
    send_message("NEXT")
