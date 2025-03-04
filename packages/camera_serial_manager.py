#!/usr/bin/env python3

import os
import subprocess
import threading
import time

import serial
from picamera2 import Picamera2

from packages.config import (ARDUINO_CLI_PATH, BAUD_RATE, CONFIG_FILE,
                             FIRMWARE_DIR, FQBN, IMAGES_DIR, SERIAL_PORT,
                             TEMPLATE_FILE)
from packages.logger import log_message


class CameraSerialManager:
    def __init__(self):
        """Initialisiert Kamera und serielle Verbindung."""
        self.PASS_COUNT = 0  # Startwert
        self.MOVE_COUNT = 0  # Startwert
        self.picam = None
        self.serial_connection = None
        self.polling_thread = None
        self.polling_active = None
        self.init_camera()
        self.init_serial()

    def init_camera(self):
        """Sichere Initialisierung der Kamera mit Fehlerprüfung."""
        log_message("Starte init_camera...", "info")
        try:
            self.picam = Picamera2()
            time.sleep(2)  # Wartezeit für Kamera-Initialisierung

            if self.picam is None:
                log_message("Kamera konnte nicht initialisiert werden!", "error")
                return

            log_message("Kamera erfolgreich erstellt.", "info")

            # DEBUG: Liste der Kamera-Modi abrufen
            log_message(f"Kamera-Modi: {self.picam.sensor_modes}", "debug")

            # Prüfen, ob Kamera verfügbar ist
            if not hasattr(self.picam, "camera_config"):
                log_message("Kamera-Konfiguration ist nicht verfügbar!", "error")
                return

            log_message("Kamera wird konfiguriert...", "info")
            self.picam.configure(self.picam.create_still_configuration())
            self.picam.start_preview()

            if self.picam.started:
                log_message("Kamera läuft bereits, überspringe start().", "info")
            else:
                log_message("Kamera wird gestartet...", "info")
                self.picam.start()

            log_message("Kamera erfolgreich gestartet.", "info")

        except Exception as e:
            log_message(f"Kamera-Fehler: {e}", "error")
            self.picam = None

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

    def generate_config_file(self, REPEATS, PAUSE_MS):
        """
        Liest config_template.h, ersetzt Platzhalter und schreibt config.h.
        """
        log_message("Generiere config.h...", "info")
        try:
            with open(TEMPLATE_FILE, "r") as template:
                content = template.read()

            # Platzhalter ersetzen
            content = content.replace("{{REPEATS_PLACEHOLDER}}", str(REPEATS))
            content = content.replace("{{PAUSE_PLACEHOLDER}}", str(PAUSE_MS))

            # Neue config.h schreiben
            with open(CONFIG_FILE, "w") as config:
                config.write(content)

            log_message("config.h wurde erfolgreich generiert.")

        except FileNotFoundError:
            log_message(f"FEHLER: {TEMPLATE_FILE} wurde nicht gefunden.", "error")

    # SKETCH KOMPILIEREN
    def compile_sketch(self):
        """Ruft arduino-cli compile auf."""
        log_message("Kompiliere Sketch...", "info")
        try:
            subprocess.run(
                [ARDUINO_CLI_PATH, "compile", "--fqbn", FQBN, FIRMWARE_DIR], check=True
            )
            log_message("Kompilierung erfolgreich.", "info")
        except subprocess.CalledProcessError as e:
            log_message(f"Fehler bei der Kompilierung: {e}", "error")

    # SKETCH HOCHLADEN
    def upload_sketch(self):
        """Ruft arduino-cli upload auf."""
        log_message("Lade hoch...", "info")
        try:
            subprocess.run(
                [
                    ARDUINO_CLI_PATH,
                    "upload",
                    "-p",
                    SERIAL_PORT,
                    "--fqbn",
                    FQBN,
                    FIRMWARE_DIR,
                ],
                check=True,
            )
            log_message("Upload erfolgreich.", "info")
        except subprocess.CalledProcessError as e:
            log_message(f"Fehler beim Upload: {e}", "error")

    # Polling
    def start_polling(self):
        """Startet das Polling in einem separaten Thread."""
        if hasattr(self, "polling_thread") and self.polling_thread is not None:
            log_message("Polling-Thread läuft bereits!", "warning")
            return

        log_message("Starte Arduino-Polling-Thread...")
        self.polling_active = True
        self.polling_thread = threading.Thread(target=self.poll_arduino, daemon=True)
        self.polling_thread.start()

    def poll_arduino(self):
        """Liest Daten von der seriellen Verbindung im Thread."""
        if not self.serial_connection or not self.serial_connection.is_open:
            log_message("Serielle Verbindung nicht verfügbar!", "error")
            return

        while self.polling_active:
            try:
                if self.serial_connection.in_waiting > 0:
                    raw_line = (
                        self.serial_connection.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )

                    # Debugging-Log
                    log_message(f"DEBUG: Empfangene Zeile: {raw_line}")

                    # Falls die Nachricht im falschen Format ist, logge sie
                    if not raw_line.startswith("<") or not raw_line.endswith(">"):
                        log_message(
                            f"Ungültiges Format empfangen: {raw_line}",
                            "warning",
                        )
                        continue

                    # Inhalt extrahieren
                    command = raw_line[1:-1]

                    if command == "MOVE_COMPLETED":
                        log_message(
                            "'MOVE_COMPLETED' empfangen, nehme Foto auf.", "info"
                        )
                        self.take_photo(self.PASS_COUNT, self.MOVE_COUNT)
                        self.MOVE_COUNT += 1
                        self.send_command("NEXT")
                    elif command == "DONE":
                        log_message("'DONE' empfangen, beende Polling.", "info")
                        self.stop_polling()

            except Exception as e:
                log_message(f"Fehler im Polling: {e}", "error")
                break

            time.sleep(0.1)  # CPU-Last reduzieren

    def stop_polling(self):
        """Beendet den Polling-Thread sicher."""
        log_message("Beende Arduino-Polling-Thread...")
        self.polling_active = False
        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_thread.join(timeout=2)
        self.polling_thread = None

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
