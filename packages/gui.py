#!/usr/bin/env python3

import os
import subprocess
import time
import tkinter as tk
from tkinter import ttk

from .camera import init_camera, manual_take_photo
from .config import (ARDUINO_CLI_PATH, BASE_OUTPUT_DIR, CONFIG_FILE, FQBN,
                     SERIAL_PORT, TEMPLATE_FILE)
from .logger import log_message, setup_logging
from .serial_comm import on_manual_next, poll_arduino, send_message

logger = setup_logging()


class Paparazzo(tk.Tk):
    """
    Hauptklasse für die Tkinter-GUI.
    Enthält die gesamte Logik für:
    - Arduino-Kommunikation (Senden/Empfangen)
    - Kamera (Picamera2) für Einzelfotos
    - Workflow (mehrere Durchläufe, Ordnerstruktur)
    - Log-Ausgabe in Text-Widget
    - Vollbildmodus
    """

    picam = None

    def __init__(self):
        super().__init__()
        self.title("Paparazzo GUI")
        # Logger initialisieren
        self.logger = setup_logging()
        self.logger.info("Starte Paparazzo GUI...")
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        # Fenster auf volle Bildschirmgröße, aber nicht im "echten" Vollbild
        self.geometry(f"{w}x{h}+0+0")

        # 1) Zuerst GUI-Elemente erstellen
        self.create_widgets()

        # 2) Dann Kamera initialisieren (log_message() braucht schon log_text!)
        init_camera()

        # 3) Zum Schluss Polling für Arduino starten
        poll_arduino(self)

    def create_widgets(self):
        """Erstellt alle Tkinter-Widgets und legt das Layout fest."""
        # Spaltenanpassung
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Wiederholungen: [<] [Textfeld] [>]
        REPEATS_frame = ttk.Frame(self)
        REPEATS_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        tk.Label(REPEATS_frame, text="Wiederholungen:", anchor="e").grid(
            row=0, column=0, padx=5
        )
        self.REPEATS_var = tk.IntVar(value=2)
        minus_REPEATS = ttk.Button(
            REPEATS_frame, text="<", command=self.decrement_REPEATS, width=3
        )
        minus_REPEATS.grid(row=0, column=1, padx=5, ipadx=10, ipady=10)
        REPEATS_entry = ttk.Entry(
            REPEATS_frame,
            textvariable=self.REPEATS_var,
            width=5,
            font=("Helvetica", 16),
            justify="center",
        )
        REPEATS_entry.grid(row=0, column=2, padx=5)
        plus_REPEATS = ttk.Button(
            REPEATS_frame, text=">", command=self.increment_REPEATS, width=3
        )
        plus_REPEATS.grid(row=0, column=3, padx=5, ipadx=10, ipady=10)

        # Pause (in Minuten): [<] [Textfeld] [>]
        PAUSE_frame = ttk.Frame(self)
        PAUSE_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        tk.Label(PAUSE_frame, text="Pause (Minuten):", anchor="e").grid(
            row=0, column=0, padx=5
        )
        self.PAUSE_var = tk.IntVar(value=1)
        minus_PAUSE = ttk.Button(
            PAUSE_frame, text="<", command=self.decrement_PAUSE, width=3
        )
        minus_PAUSE.grid(row=0, column=1, padx=5, ipadx=10, ipady=10)
        PAUSE_entry = ttk.Entry(
            PAUSE_frame,
            textvariable=self.PAUSE_var,
            width=5,
            font=("Helvetica", 16),
            justify="center",
        )
        PAUSE_entry.grid(row=0, column=2, padx=5)
        plus_PAUSE = ttk.Button(
            PAUSE_frame, text=">", command=self.increment_PAUSE, width=3
        )
        plus_PAUSE.grid(row=0, column=3, padx=5, ipadx=10, ipady=10)

        # Buttons: Generieren & Hochladen | Manueller NEXT
        button_frame1 = ttk.Frame(self)
        button_frame1.grid(row=2, column=0, columnspan=2, pady=5)
        gen_upload_btn = ttk.Button(
            button_frame1,
            text="Generieren & Hochladen",
            command=self.on_generate_and_upload,
            width=22,
        )
        gen_upload_btn.grid(row=0, column=0, padx=5)
        manual_next_btn = ttk.Button(
            button_frame1, text="Manueller NEXT", command=on_manual_next, width=22
        )
        manual_next_btn.grid(row=0, column=1, padx=5)

        # Buttons: Programm START | Manuelles Foto
        button_frame2 = ttk.Frame(self)
        button_frame2.grid(row=3, column=0, columnspan=2, pady=5)
        start_btn = ttk.Button(
            button_frame2,
            text="Programm START",
            command=self.on_start_program,
            width=22,
        )
        start_btn.grid(row=0, column=0, padx=5)
        photo_btn = ttk.Button(
            button_frame2,
            text="Manuelles Foto",
            command=manual_take_photo,
            width=22,
        )
        photo_btn.grid(row=0, column=1, padx=5)

        # Button: Abbruch (zentriert)
        abort_btn = ttk.Button(self, text="Abbruch", command=self.on_abort, width=22)
        abort_btn.grid(row=4, column=0, columnspan=2, pady=5)

        # Log-Text + Scrollbar
        self.log_text = tk.Text(self, wrap="word", height=15, width=70)
        self.log_text.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")
        self.log_text["yscrollcommand"] = scrollbar.set

    def on_start_program(self):
        """
        Wird aufgerufen, wenn "Programm START" geklickt wird.
        1) Legt einen neuen Hauptordner an.
        2) Liest REPEATS aus GUI.
        3) Legt den ersten Pass-Unterordner an.
        4) Schickt 'START' an Arduino.
        """
        now_str = time.strftime("run_%Y%m%d_%H%M%S")
        self.RUN_DIR = os.path.join(BASE_OUTPUT_DIR, now_str)
        os.makedirs(self.RUN_DIR, exist_ok=True)
        log_message(f"Neuer Lauf-Ordner: {self.RUN_DIR}")

        REPEATS = self.REPEATS_var.get()
        if REPEATS < 1:
            log_message(
                logger, "Bitte eine Zahl größer als 0 für Wiederholungen eingeben."
            )
            return
        self.REPEATS = REPEATS

        # Pass 1 beginnen
        self.PASS_COUNT = 1
        self.MOVE_COUNT = 0
        self.start_pass_folder()

        log_message("Sende 'START' an Arduino...")
        send_message("START")

    def start_pass_folder(self):
        """Legt den Unterordner (pass_01, pass_02, ...) für den aktuellen Pass an."""
        # Falls self.RUN_DIR noch nicht gesetzt ist, verwende BASE_OUTPUT_DIR als Fallback
        BASE_DIR = self.RUN_DIR if self.RUN_DIR is not None else BASE_OUTPUT_DIR
        PASS_FOLDER_NAME = f"pass_{self.PASS_COUNT:02d}"
        self.CURRENT_PASS_DIR = os.path.join(BASE_DIR, PASS_FOLDER_NAME)
        os.makedirs(self.CURRENT_PASS_DIR, exist_ok=True)
        log_message(logger, f"Neuer Pass-Ordner angelegt: {self.CURRENT_PASS_DIR}")
        self.MOVE_COUNT = 0

    # Input button functions
    def increment_REPEATS(self):
        self.REPEATS_var.set(self.REPEATS_var.get() + 1)

    def decrement_REPEATS(self):
        if self.REPEATS_var.get() > 1:
            self.REPEATS_var.set(self.REPEATS_var.get() - 1)

    def increment_PAUSE(self):
        self.PAUSE_var.set(self.PAUSE_var.get() + 1)

    def decrement_PAUSE(self):
        if self.PAUSE_var.get() > 1:
            self.PAUSE_var.set(self.PAUSE_var.get() - 1)

    # KONFIGURATION GENERIEREN
    def generate_config_file(self, REPEATS, PAUSE):
        """
        Liest config_template.h, ersetzt Platzhalter und schreibt config.h
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

            print("config.h wurde erfolgreich generiert.")

        except FileNotFoundError:
            print(f"FEHLER: {TEMPLATE_FILE} wurde nicht gefunden.")

    # GENERIEREN & HOCHLADEN
    def on_generate_and_upload(self):
        """Button-Klick: Erstellt config.h, kompiliert und lädt den Sketch hoch."""
        REPEATS = self.REPEATS_var.get()
        PAUSE_MS = self.PAUSE_var.get()

        if REPEATS < 1:
            log_message("Bitte eine Zahl größer als 0 für Wiederholungen eingeben.")
            return
        if PAUSE_MS < 1:
            log_message("Bitte eine Zahl größer als 0 für Pause (Minuten) eingeben.")
            return

        # Werte
        REPEATS = int(REPEATS)
        PAUSE_MS = int(PAUSE_MS)

        # 1) config.h generieren
        self.generate_config_file(REPEATS, PAUSE_MS)
        log_message("Generiere config.h...")

        # 2) Kompilieren
        self.compile_sketch()
        log_message("Kompiliere Sketch...")

        # 3) Hochladen
        self.upload_sketch()
        log_message("Lade hoch...")

        log_message("Fertig!")

    # SKETCH KOMPILIEREN
    def compile_sketch(self):
        """Ruft arduino-cli compile auf."""
        try:
            subprocess.run(
                [ARDUINO_CLI_PATH, "compile", "--fqbn", FQBN, "."], check=True
            )
            log_message("Kompilierung erfolgreich.")
        except subprocess.CalledProcessError as e:
            log_message(f"Fehler bei der Kompilierung: {e}")

    # SKETCH HOCHLADEN
    def upload_sketch(self):
        """Ruft arduino-cli upload auf."""
        try:
            subprocess.run(
                [ARDUINO_CLI_PATH, "upload", "-p", SERIAL_PORT, "--fqbn", FQBN, "."],
                check=True,
            )
            log_message("Upload erfolgreich.")
        except subprocess.CalledProcessError as e:
            log_message(f"Fehler beim Upload: {e}")

    # ABBRECHEN
    def on_abort(self):
        """Button-Klick: Sende 'ABORT' an Arduino, der daraufhin abbrechen soll."""
        log_message("Sende 'ABORT' an Arduino...")
        send_message("abort")


def main():
    app = Paparazzo()
    app.mainloop()


# STARTPUNKT
if __name__ == "__main__":
    main()
