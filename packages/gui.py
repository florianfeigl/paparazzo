#!/usr/bin/env python3

import os
import time
import tkinter as tk
from tkinter import ttk

from packages.camera_serial_manager import CameraSerialManager
from packages.config import IMAGES_DIR, PASS_COUNT, RUN_DIR
from packages.logger import (gui_instance, log_message, set_gui_instance,
                             setup_logging)

# Logger zuweisen
logger = setup_logging()


class Paparazzo(tk.Tk):
    """
    Hauptklasse für die Tkinter-GUI.
    """

    picam = None

    def __init__(self):
        super().__init__()
        global gui_instance

        # GUI Titel
        self.title("Paparazzo GUI")

        # GUI Darstellung
        style = ttk.Style()
        style.theme_use("clam")  # Alternativ: 'alt', 'default', 'classic'
        style.configure("CenterEntry.TEntry", padding=(0, 10, 0, 10))

        # Fenster maximiert starten
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+0+0")

        # 1) Zuerst GUI-Elemente erstellen
        self.create_widgets()

        # `log_text` Existenzcheck
        if not hasattr(self, "log_text"):
            log_message("log_text Widget existiert nicht!", "error")
            return

        # Manager für Kamera & serielle Schnittstelle
        set_gui_instance(self)

        # Logger initialisieren
        self.logger = setup_logging()
        log_message("Starte Paparazzo GUI...", "info")
        log_message("Initialisiere Log System...", "info")

        self.manager = CameraSerialManager()  # führt init_camera bereits aus!

        # 3) Zum Schluss Polling für Arduino starten
        self.after(100, self.manager.start_polling)

    def create_widgets(self):
        """Erstellt alle Tkinter-Widgets und legt das Layout fest."""
        # Spaltenanpassung
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Reihen in Spalte 1
        # Wiederholungen: [<] [Textfeld] [>]
        repeats_frame = ttk.Frame(self)
        repeats_frame.grid(row=0, column=0, padx=10)
        self.repeats_var = tk.IntVar(value=2)
        minus_repeats = ttk.Button(
            repeats_frame, text="<", command=self.decrement_repeats, width=7
        )
        minus_repeats.grid(row=0, column=0, padx=10, ipadx=14, ipady=14)
        repeats_entry = ttk.Entry(
            repeats_frame,
            textvariable=self.repeats_var,
            width=3,
            font=("Helvetica", 26),
            justify="center",
            style="CenterEntry.TEntry",
        )
        repeats_entry.grid(row=0, column=1)
        plus_repeats = ttk.Button(
            repeats_frame, text=">", command=self.increment_repeats, width=7
        )
        plus_repeats.grid(row=0, column=2, padx=10, ipadx=14, ipady=14)
        tk.Label(repeats_frame, text="Wiederholungen (Standard: 2)", anchor="e").grid(
            row=1, column=0, columnspan=3, padx=20
        )

        # Pause (in Minuten): [<] [Textfeld] [>]
        pause_frame = ttk.Frame(self)
        pause_frame.grid(row=1, column=0, padx=10)
        tk.Label(pause_frame, text="Pause Minuten (Standard: 1)", anchor="e").grid(
            row=0, column=0, columnspan=3, padx=10
        )
        self.pause_var = tk.IntVar(value=1)
        minus_pause = ttk.Button(
            pause_frame, text="<", command=self.decrement_pause, width=7
        )
        minus_pause.grid(row=1, column=0, padx=20, ipadx=14, ipady=14)
        pause_entry = ttk.Entry(
            pause_frame,
            textvariable=self.pause_var,
            width=3,
            font=("Helvetica", 25),
            justify="center",
            style="CenterEntry.TEntry",
        )
        pause_entry.grid(row=1, column=1)
        plus_pause = ttk.Button(
            pause_frame, text=">", command=self.increment_pause, width=7
        )
        plus_pause.grid(row=1, column=2, padx=20, ipadx=14, ipady=14)

        # Reihen in Spalte 2
        # Generieren & Hochladen
        gen_upload_btn = ttk.Button(
            self,
            text="GENERIEREN & LADEN",
            command=self.on_generate_and_upload,
            width=18,
        )
        gen_upload_btn.grid(row=0, column=1, ipadx=14, ipady=14)

        # Programm START
        start_btn = ttk.Button(
            self,
            text="STARTEN",
            command=self.on_start_program,
            width=18,
        )
        start_btn.grid(row=1, column=1, padx=10, ipadx=14, ipady=14)

        # Reihen in Spalte 3
        # Programm ABBRUCH
        abort_btn = ttk.Button(
            self, text="ZURÜCKSETZEN", command=self.on_abort, width=18
        )
        abort_btn.grid(row=0, column=2, padx=10, ipadx=14, ipady=14)

        # Programm SCHLIESSEN
        close_button = ttk.Button(
            self, text="SCHLIESSEN", command=self.on_close, width=20
        )
        close_button.grid(row=1, column=2, padx=10, ipadx=14, ipady=14)

        # Log-Text-Widget initialisieren
        self.log_text = tk.Text(self, wrap="word", height=15, width=25)
        self.log_text.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Scrollbar für das Log-Text-Widget
        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=5, column=3, sticky="ns")  # Scrollbar in column 2
        self.log_text["yscrollcommand"] = scrollbar.set

        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=5, column=3, sticky="ns")

        # WICHTIG: Das Text-Widget muss dem Scrollbar mitteilen, wann es gescrollt wird.
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # MANUELLE AKTIONEN
        ## Manual NEXT
        ## Manual PHOTO

    # GENERIEREN & HOCHLADEN
    def on_generate_and_upload(self):
        """Button-Klick: Erstellt config.h, kompiliert und lädt den Sketch hoch."""
        REPEATS = self.repeats_var.get()
        PAUSE_MS = self.pause_var.get()

        if REPEATS < 1:
            log_message(
                "Unzulässige Eingabe. Bitte eine Zahl größer als 0 für Wiederholungen eingeben.",
                "error",
            )
            return
        if PAUSE_MS < 1:
            log_message(
                "Unzulässige Eingabe. Bitte eine Zahl größer als 0 für Pause (Minuten) eingeben.",
                "error",
            )
            return

        # Werte
        REPEATS = int(REPEATS)
        PAUSE_MS = int(PAUSE_MS)

        # 1) config.h generieren
        self.manager.generate_config_file(REPEATS, PAUSE_MS)

        # 2) Kompilieren
        self.manager.compile_sketch()

        # 3) Hochladen
        self.manager.upload_sketch()

        log_message("Fertig!", "info")

    def start_pass_folder(self):
        """Legt den Unterordner (pass_01, pass_02, ...) für den aktuellen Pass an."""
        # Falls self.RUN_DIR noch nicht gesetzt ist, verwende IMAGES_DIR als Fallback
        BASE_DIR = RUN_DIR if RUN_DIR is not None else IMAGES_DIR
        PASS_FOLDER_NAME = f"pass_{PASS_COUNT:02d}"
        self.CURRENT_PASS_DIR = os.path.join(BASE_DIR, PASS_FOLDER_NAME)
        os.makedirs(self.CURRENT_PASS_DIR, exist_ok=True)
        log_message(f"Neuer Pass-Ordner angelegt: {self.CURRENT_PASS_DIR}", "info")
        self.MOVE_COUNT = 0

    # Input button functions
    def increment_repeats(self):
        self.repeats_var.set(self.repeats_var.get() + 1)

    def decrement_repeats(self):
        if self.repeats_var.get() > 1:
            self.repeats_var.set(self.repeats_var.get() - 1)

    def increment_pause(self):
        self.pause_var.set(self.pause_var.get() + 1)

    def decrement_pause(self):
        if self.pause_var.get() > 1:
            self.pause_var.set(self.pause_var.get() - 1)

    # ABBRECHEN
    def on_abort(self):
        """Button-Klick: Sende 'ABORT' an Arduino, der daraufhin abbrechen soll."""
        log_message("Sende 'ABORT' an Arduino...", "info")
        self.manager.send_command("ABORT")

    # SCHLIESSEN
    def on_close(self):
        """Sauberes Beenden der GUI und aller verbundenen Prozesse."""
        log_message("Beende Programm...", "info")

        # 1️⃣ Falls Kamera läuft, stoppen
        if self.manager.picam:
            log_message("Stoppe Kamera...", "info")
            self.manager.picam.stop()
            log_message("Kamera gestoppt.", "info")

        # 2️⃣ Serielle Verbindung schließen, falls aktiv
        if self.manager.serial_connection and self.manager.serial_connection.is_open:
            log_message("Schließe serielle Verbindung...", "info")
            self.manager.serial_connection.close()
            log_message("Serielle Verbindung geschlossen.", "info")

        # 3️⃣ Eventuelle Threads oder laufende Funktionen beenden (z. B. `poll_arduino`)
        self.manager.stop_polling()

        # 4️⃣ Tkinter-Fenster sauber schließen
        log_message("GUI wird zerstört...", "info")
        set_gui_instance(None)
        self.destroy()

    # PROGRAMM-START
    def on_start_program(self):
        """
        Wird aufgerufen, wenn "Programm START" geklickt wird.
        1) Legt einen neuen Hauptordner an.
        2) Liest REPEATS aus GUI.
        3) Legt den ersten Pass-Unterordner an.
        4) Schickt 'START' an Arduino.
        """
        now_str = time.strftime("run_%Y%m%d_%H%M%S")
        RUN_DIR = os.path.join(IMAGES_DIR, now_str)
        os.makedirs(RUN_DIR, exist_ok=True)
        log_message(f"Neuer Lauf-Ordner: {RUN_DIR}", "info")

        REPEATS = self.repeats_var.get()
        if REPEATS < 1:
            log_message(
                "Unzulässige Eingabe. Bitte eine Zahl größer als 0 für Wiederholungen eingeben.",
                "error",
            )
            return

        self.start_pass_folder()

        log_message("Sende 'START' an Arduino...", "info")
        self.manager.send_command("START")


def main():
    app = Paparazzo()
    app.mainloop()


if __name__ == "__main__":
    main()
