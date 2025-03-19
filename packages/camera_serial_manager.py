#!/usr/bin/env python3

import os
import subprocess
import threading
import time

import serial
from picamera2 import Picamera2

from packages.config import (ARDUINO_CLI_PATH, BAUD_RATE, CONFIG_FILE,
                             FIRMWARE_DIR, FQBN, IMAGES_DIR, POSITIONS_COLUMN,
                             POSITIONS_ROW, SERIAL_PORT, TEMPLATE_FILE,
                             TOTAL_STATIONS)
from packages.logger import log_message


class CameraSerialManager:
    def __init__(self, gui=None):
        """Initialisiert Kamera und serielle Verbindung."""
        self.gui = gui
        self.PASS_COUNT = 0  # Startwert
        self.MOVE_COUNT = 0  # Startwert
        self.picam = None
        self.serial_connection = None
        self.polling_thread = None
        self.polling_active = None
        self.run_id = time.strftime("%Y%m%d_%H%M%S")  # Setzen der run_id
        self.init_camera()
        self.init_serial()

    # Counter Value Managment
    def increment_move_count(self):
        self.MOVE_COUNT += 1

    def reset_move_count(self):
        self.MOVE_COUNT = 0

    def increment_pass_count(self):
        self.PASS_COUNT += 1

    def reset_pass_count(self):
        self.PASS_COUNT = 0

    def get_current_move_count(self):
        return self.MOVE_COUNT

    def get_current_pass_count(self):
        return self.PASS_COUNT

    # Kamera initialisieren
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
            # log_message(f"Kamera-Modi: {self.picam.sensor_modes}", "debug")

            # Prüfen, ob Kamera verfügbar ist
            if not hasattr(self.picam, "camera_config"):
                log_message("Kamera-Konfiguration ist nicht verfügbar!", "error")
                return

            log_message("Kamera wird konfiguriert...", "info")
            self.picam.configure(self.picam.create_still_configuration())

            if self.picam.started:
                log_message("Kamera läuft bereits, überspringe start().", "info")
            else:
                log_message("Kamera wird gestartet...", "info")
                self.picam.start()

            log_message("Kamera erfolgreich gestartet.", "info")

        except Exception as e:
            log_message(f"Kamera-Fehler: {e}", "error")
            self.picam = None

    # Serielle Verbindung
    def init_serial(self):
        """Öffnet die serielle Verbindung zum Arduino."""
        try:
            self.serial_connection = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            time.sleep(2)  # Arduino-Reset abwarten
            log_message(f"Serielle Verbindung geöffnet: {SERIAL_PORT}")
        except serial.SerialException as e:
            log_message(f"Fehler beim Öffnen des seriellen Ports: {e}", "error")
            self.serial_connection = None

    # Befehle an Raspberry senden und loggen
    def send_command(self, command):
        """Sendet einen Befehl an den Arduino (z. B. 'START', 'NEXT_MOVE', 'ABORT')."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write((command + "\n").encode("utf-8"))
            self.serial_connection.flush()
            log_message(f"=> Arduino: {command}")
        else:
            log_message("Serielle Verbindung nicht verfügbar!", "error")

    # Konfigurationsdatei generieren
    def generate_config_file(self, REPEATS, PAUSE):
        """
        Liest config_template.h, ersetzt Platzhalter und schreibt config.h.
        """
        if self.gui is not None:
            repeats = self.gui.repeats_var.get()
            pause = self.gui.pause_var.get() * 60000  # Umrechnung Minuten auf ms
            log_message(f"Generiere config.h mit repeats={repeats}, pause={pause}ms", "info")
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

    # Arduino Sketch kompilieren
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

    # Arduino Sketch hochladen
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

    # Polling Start Helper
    def start_polling(self):
        """Startet Polling in eigenem Thread, falls noch nicht aktiv."""
        if self.polling_thread and self.polling_thread.is_alive():
            log_message("Polling-Thread läuft bereits!", "warning")
            return

        log_message("Starte Arduino-Polling-Thread...", "info")
        self.polling_active = True
        self.polling_thread = threading.Thread(target=self.poll_arduino, daemon=True)
        self.polling_thread.start()

    # Polling Stop Helper
    def stop_polling(self):
        """Stoppt den Polling-Thread sicher und wartet auf dessen Ende."""
        log_message("Beende Arduino-Polling-Thread...", "info")
        self.polling_active = False

        if (
            self.polling_thread
            and threading.current_thread() is not self.polling_thread
        ):
            self.polling_thread.join(timeout=2)
            self.polling_thread = None

    # Restart Polling
    def restart_polling_thread(self):
        """Thread sicher beenden und nach Pause neu starten."""
        log_message("Starte Polling nach kurzer Wartezeit neu...", "info")
        self.polling_active = False  # Stoppt und räumt aktuellen Thread sauber auf
        time.sleep(1)
        self.start_polling()  # Erstellt und startet neuen Polling-Thread

    # Polling
    def poll_arduino(self):
        """Pollt den Arduino in einem separaten Thread."""
        log_message("Arduino-Abfrage gestartet.", "info")
        self.polling_active = True

        while self.polling_active:
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    if self.serial_connection.in_waiting > 0:
                        raw_line = (
                            self.serial_connection.readline()
                            .decode("utf-8", errors="ignore")
                            .strip()
                        )

                        if not raw_line.startswith("<") or not raw_line.endswith(">"):
                            continue

                        command = raw_line[1:-1]

                        if command == "MOVE_COMPLETED":
                            log_message("<= Raspberry: 'MOVE_COMPLETED'", "info")
                            self.take_photo()
                            self.increment_move_count()

                            if self.get_current_move_count() >= TOTAL_STATIONS:
                                self.increment_pass_count()

                                if self.gui.get_repeats() <= self.get_current_pass_count():
                                    log_message(f"Alle Läufe ({self.get_current_pass_count():02d}) abgeschlossen.", "info")
                                    self.send_command("END")
                                    self.polling_active = False
                                    break  # Ende des gesamten Prozesses

                                else:
                                    self.send_command("NEXT_PASS")
                                    log_message("=> Arduino: 'NEXT_PASS'", "info")

                                    self.reset_move_count()
                                    self.setup_pass_directory()

                            else:
                                self.send_command("NEXT_MOVE")
                                log_message("=> Arduino: 'NEXT_MOVE'", "info")

                else:
                    log_message("Serielle Verbindung nicht verfügbar!", "error")
                    self.polling_active = False

            except Exception as e:
                log_message(f"Fehler in der Abfrage: {e}", "error")
                self.polling_active = False

            time.sleep(0.1)

        log_message("Arduino-Abfrage beendet.", "info")

    # Laufverzeichnis erstellen
    def setup_run_directory(self):
        """Erstellt den Run-Ordner."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.run_id = f"run_{timestamp}"
        self.RUN_DIR = os.path.join(IMAGES_DIR, self.run_id)
        os.makedirs(self.RUN_DIR, exist_ok=True)
        log_message(f"Laufverzeichnis erstellt: {self.RUN_DIR}")

    # Rundenverzeichnis erstellen
    def setup_pass_directory(self):
        """Erstellt den Unterordner für den aktuellen Pass."""
        self.PASS_FOLDER_NAME = f"pass_{self.PASS_COUNT:02d}"
        self.CURRENT_PASS_DIR = os.path.join(self.RUN_DIR, self.PASS_FOLDER_NAME)
        os.makedirs(self.CURRENT_PASS_DIR, exist_ok=True)
        log_message(f"Rundenverzeichnis erstellt: {self.CURRENT_PASS_DIR}")

    # Position bestimmen
    def get_current_position(self):
        """
        Ermittelt die aktuelle Position basierend auf MOVE_COUNT.
        """
        col_index = self.MOVE_COUNT % len(POSITIONS_COLUMN)
        row_index = self.MOVE_COUNT // len(POSITIONS_COLUMN)
        col_value = POSITIONS_COLUMN[col_index]
        row_value = POSITIONS_ROW[row_index]

        return col_value, row_value

    # Bild aufnehmen
    def take_photo(self):
        log_message("Nehme Bild auf...")
        if not self.picam:
            log_message("🚨 Kamera nicht initialisiert!", "error")
            return

        sensor_size = self.picam.sensor_resolution
        width, height = sensor_size

        new_width, new_height = int(width * 0.6), int(height * 0.6)
        x = (width - new_width) // 2
        y = (height - new_height) // 2

        self.picam.set_controls({"ScalerCrop": (x, y, new_width, new_height)})
        log_message(
            f"Bildausschnitt: x={x}, y={y}, width={new_width}, height={new_height}"
        )

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        col_value, row_value = self.get_current_position()
        filename = f"{timestamp}_{row_value}{col_value}.jpg"
        filepath = os.path.join(self.CURRENT_PASS_DIR, filename)

        time.sleep(0.1)

        try:
            self.picam.capture_file(filepath)
            log_message(f"Bild aufgenommen: {filepath}")
        except Exception as e:
            log_message(f"Fehler bei der Bildaufnahme: {e}", "error")
