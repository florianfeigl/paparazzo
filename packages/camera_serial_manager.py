#!/usr/bin/env python3

import os
import subprocess
import time

import serial
from picamera2 import Picamera2

from packages.config import (ARDUINO_CLI_PATH, BAUD_RATE, CONFIG_FILE, FQBN,
                             IMAGES_DIR, MOVE_COUNT, PASS_COUNT, SERIAL_PORT,
                             TEMPLATE_FILE)
from packages.logger import log_message


class CameraSerialManager:
    def __init__(self):
        """Initialisiert Kamera und serielle Verbindung."""
        self.picam = None
        self.serial_connection = None
        self.PASS_COUNT = 1  # Startwert
        self.MOVE_COUNT = 0  # Startwert
        self.init_camera()
        self.init_serial()

    def init_camera(self):
        """Sichere Initialisierung der Kamera mit Fehlerprüfung."""
        log_message("Starte init_camera...")
        try:
            self.picam = Picamera2()
            time.sleep(2)  # Wartezeit für Kamera-Initialisierung

            if self.picam is None:
                log_message(
                    "[ERROR] Kamera konnte nicht initialisiert werden!", "error"
                )
                return

            log_message("[INFO] Kamera erfolgreich erstellt.")

            # DEBUG: Liste der Kamera-Modi abrufen
            log_message(f"[DEBUG] Kamera-Modi: {self.picam.sensor_modes}")

            # Falls `camera_config` None ist, weiter abbrechen
            if self.picam.camera_config is None:
                log_message("[ERROR] Kamera-Konfiguration ist None!", "error")
                return

            log_message("[INFO] Kamera wird konfiguriert...")
            self.picam.configure(self.picam.create_still_configuration())
            self.picam.start_preview()

            log_message("[INFO] Kamera wird gestartet...")
            self.picam.start()

            log_message("[INFO] Kamera erfolgreich gestartet.")

       # except Exception as e:
       #     log_message(f"[ERROR] Kamera-Fehler: {e}", "error")
       #     self.picam = None

    def init_serial(self):
        """Öffnet die serielle Verbindung zum Arduino."""
        try:
            self.serial_connection = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            time.sleep(2)  # Arduino-Reset abwarten
            log_message(f"Serielle Verbindung geöffnet: {SERIAL_PORT}")
        except serial.SerialException as e:
            log_message(f"Fehler beim Öffnen des seriellen Ports: {e}", "error")
            self.serial_connection = None

    def send_command(self, command):
        """Sendet einen Befehl an den Arduino (z. B. 'START', 'NEXT', 'ABORT')."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write((command + "\n").encode("utf-8"))
            self.serial_connection.flush()
            log_message(f"=> Arduino: {command}")
        else:
            log_message("Serielle Verbindung nicht verfügbar!", "error")

    def generate_config_file(self, REPEATS, PAUSE):
        """
        Liest config_template.h, ersetzt Platzhalter und schreibt config.h.
        """
        try:
            with open(TEMPLATE_FILE, "r") as template:
                content = template.read()

            # Platzhalter ersetzen
            content = content.replace("{{REPEATS_PLACEHOLDER}}", str(REPEATS))
            content = content.replace("{{PAUSE_PLACEHOLDER}}", str(PAUSE))

            # Neue config.h schreiben
            with open(CONFIG_FILE, "w") as config:
                config.write(content)

            log_message("config.h wurde erfolgreich generiert.")

        except FileNotFoundError:
            log_message(f"FEHLER: {TEMPLATE_FILE} wurde nicht gefunden.", "error")

    # SKETCH KOMPILIEREN
    def compile_sketch(self):
        """Ruft arduino-cli compile auf."""
        try:
            subprocess.run(
                [ARDUINO_CLI_PATH, "compile", "--fqbn", FQBN, "."], check=True
            )
            log_message("Kompilierung erfolgreich.", "info")
        except subprocess.CalledProcessError as e:
            log_message(f"Fehler bei der Kompilierung: {e}", "error")

    # SKETCH HOCHLADEN
    def upload_sketch(self):
        """Ruft arduino-cli upload auf."""
        try:
            subprocess.run(
                [ARDUINO_CLI_PATH, "upload", "-p", SERIAL_PORT, "--fqbn", FQBN, "."],
                check=True,
            )
            log_message("Upload erfolgreich.", "info")
        except subprocess.CalledProcessError as e:
            log_message(f"Fehler beim Upload: {e}", "error")

    # DATENABFRAGE
    def poll_arduino(self):
        """Liest Arduino-Antworten und verarbeitet sie."""
        if not (self.serial_connection and self.serial_connection.is_open):
            log_message("Serielle Verbindung nicht offen – kann nicht pollen.", "error")
            return

        while True:
            try:
                line = (
                    self.serial_connection.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                if line:
                    log_message(f"Arduino: {line}")
                    if line == "MOVE_COMPLETED":
                        # `pass_count` und `move_count` übergeben
                        self.take_photo(PASS_COUNT, MOVE_COUNT)
                        self.MOVE_COUNT += 1  # Zähler hochzählen

                        # Sende 'NEXT', falls noch Bewegungen ausstehen
                        self.send_command("NEXT")

                    elif line == "DONE":
                        log_message("Arduino-Prozess abgeschlossen.")
                        break  # Polling beenden

            except Exception as e:
                log_message(f"Fehler beim Lesen der seriellen Verbindung: {e}", "error")
                break  # Falls Fehler auftritt, Polling abbrechen

    def take_photo(self, PASS_COUNT, MOVE_COUNT):
        """Nimmt ein Foto auf und speichert es mit einem passenden Dateinamen."""
        if not self.picam:
            log_message("Kamera nicht verfügbar!", "error")
            return

        # Bestimme die Dateistruktur
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"photo_pass{PASS_COUNT}_move{MOVE_COUNT}_{timestamp}.jpg"
        folder = os.path.join(IMAGES_DIR, f"pass_{PASS_COUNT:02d}")
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)

        try:
            self.picam.capture_file(filepath)
            log_message(f"Foto aufgenommen: {filepath}")
        except Exception as e:
            log_message(f"Fehler bei der Fotoaufnahme: {e}", "error")

    def read_arduino_response(self):
        """Liest eine Zeile von der seriellen Schnittstelle."""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None

        try:
            raw_line = (
                self.serial_connection.readline()
                .decode("utf-8", errors="ignore")
                .strip()
            )
            if raw_line.startswith("<") and raw_line.endswith(">"):
                return raw_line[1:-1]  # Entferne die eckigen Klammern <...>
            return raw_line
        except Exception as e:
            log_message(f"Fehler beim Lesen der seriellen Verbindung: {e}", "error")
            return None
