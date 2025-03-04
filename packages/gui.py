#!/usr/bin/env python3

import os
import time
import tkinter as tk
from tkinter import ttk

from packages.camera_serial_manager import CameraSerialManager
from packages.config import IMAGES_DIR, PASS_COUNT, RUN_DIR
from packages.logger import set_gui_instance, gui_instance, log_message, setup_logging

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

        # Setze das Theme für eine bessere Darstellung
        style = ttk.Style()
        style.theme_use("clam")  # Alternativ: 'alt', 'default', 'classic'
        style.configure("CenterEntry.TEntry", padding=(0, 10, 0, 10))

        # Fenster maximiert starten
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+0+0")

        # Manager für Kamera & serielle Schnittstelle
        self.manager = CameraSerialManager()

        # 1) Zuerst GUI-Elemente erstellen
        self.create_widgets()

        set_gui_instance(self)
        # Logger initialisieren
        self.logger = setup_logging()
        log_message("Starte Paparazzo GUI...", "info")

        # 2) Dann Kamera initialisieren (logger() braucht schon log_text!)
        self.manager.init_camera()

        # 3) Zum Schluss Polling für Arduino starten
        self.after(100, self.manager.poll_arduino)  

    def create_widgets(self):
        """Erstellt alle Tkinter-Widgets und legt das Layout fest."""
        # Spaltenanpassung
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Wiederholungen: [<] [Textfeld] [>]
        repeats_frame = ttk.Frame(self)
        repeats_frame.grid(row=0, column=0, padx=10)
        tk.Label(repeats_frame, text="Wiederholungen:", anchor="e").grid(
            row=0, column=0, columnspan=3, padx=10, pady=5
        )
        self.repeats_var = tk.IntVar(value=2)
        minus_repeats = ttk.Button(
            repeats_frame, text="<", command=self.decrement_repeats, width=5
        )
        minus_repeats.grid(row=1, column=0, padx=10, ipadx=10, ipady=14)
        repeats_entry = ttk.Entry(
            repeats_frame,
            textvariable=self.repeats_var,
            width=3,
            font=("Helvetica", 26),
            justify="center",
            style="CenterEntry.TEntry",
        )
        repeats_entry.grid(row=1, column=1)
        plus_repeats = ttk.Button(
            repeats_frame, text=">", command=self.increment_repeats, width=5
        )
        plus_repeats.grid(row=1, column=2, padx=10, ipadx=10, ipady=14)

        # Pause (in Minuten): [<] [Textfeld] [>]
        pause_frame = ttk.Frame(self)
        pause_frame.grid(row=1, column=0, padx=10)
        tk.Label(pause_frame, text="Pause (Minuten):", anchor="e").grid(
            row=0, column=0, columnspan=3, padx=10, pady=5
        )
        self.pause_var = tk.IntVar(value=1)
        minus_pause = ttk.Button(
            pause_frame, text="<", command=self.decrement_pause, width=5
        )
        minus_pause.grid(row=1, column=0, padx=10, ipadx=10, ipady=14)
        pause_entry = ttk.Entry(
            pause_frame,
            textvariable=self.pause_var,
            width=3,
            font=("Helvetica", 26),
            justify="center",
            style="CenterEntry.TEntry",
        )
        pause_entry.grid(row=1, column=1)
        plus_pause = ttk.Button(
            pause_frame, text=">", command=self.increment_pause, width=5
        )
        plus_pause.grid(row=1, column=2, padx=10, ipadx=10, ipady=14)

        # Generieren & Hochladen
        gen_upload_btn = ttk.Button(
            self,
            text="Generieren & Hochladen",
            command=self.on_generate_and_upload,
            width=25,
        )
        gen_upload_btn.grid(row=2, column=0, pady=10, ipadx=14, ipady=14)

        # PROGRAMMFUNKTIONEN
        # Programm START
        start_btn = ttk.Button(
            self,
            text="Programm START",
            command=self.on_start_program,
            width=20,
        )
        start_btn.grid(row=0, column=1, padx=10, ipadx=14, ipady=14)

        # Programm ABBRUCH
        abort_btn = ttk.Button(
            self, text="Programm ABBRUCH", command=self.on_abort, width=20
        )
        abort_btn.grid(row=1, column=1, padx=10, ipadx=14, ipady=14)

        # Programm SCHLIESSEN
        close_button = ttk.Button(
            self, text="Programm SCHLIESSEN", command=self.on_close, width=20
        )
        close_button.grid(row=2, column=1, padx=10, ipadx=14, ipady=14)

        # Log-Text + Scrollbar
        self.log_text = tk.Text(self, wrap="word", height=50, width=70)
        self.log_text.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")

        # WICHTIG: Das Text-Widget muss dem Scrollbar mitteilen, wann es gescrollt wird.
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # MANUELLE AKTIONEN
        ## Manual NEXT
        # manual_next_btn = ttk.Button(
        #    button_frame1,
        #    text="Manueller NEXT",
        #    command=on_manual_next,
        #    width=20,
        # )
        # manual_next_btn.grid(row=0, column=2, padx=10, ipadx=7, ipady=7)
        ## Manual PHOTO
        # photo_btn = ttk.Button(
        #    button_frame2,
        #    text="Manuelles Foto",
        #    command=manual_take_photo,
        #    width=20,
        # )
        # photo_btn.grid(row=0, column=1, padx=10, ipadx=7, ipady=7)

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
        log_message("Generiere config.h...", "info")

        # 2) Kompilieren
        self.manager.compile_sketch()
        log_message("Kompiliere Sketch...", "info")

        # 3) Hochladen
        self.manager.upload_sketch()
        log_message("Lade hoch...", "info")

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
        log_message("Programm beendet.", "info")
        Paparazzo.destroy(self)

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

        REPEATS = REPEATS

        self.start_pass_folder()

        log_message("Sende 'START' an Arduino...", "info")
        self.manager.send_command("START")


def main():
    app = Paparazzo()
    app.mainloop()


# STARTPUNKT
if __name__ == "__main__":
    main()
