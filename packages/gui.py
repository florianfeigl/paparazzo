# GUI

import datetime
import os
import subprocess
import time
import tkinter as tk
from tkinter import ttk

from .camera import init_camera, poll_arduino, send_message
from .config import (ARDUINO_CLI_PATH, BASE_OUTPUT_DIR, CONFIG_FILE, FQBN,
                     SERIAL_PORT, TEMPLATE_FILE)
from .logger import setup_logging


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

        # Row/Column-Listen und total_stations
        self.positions_column = [1, 2, 3, 4, 5, 6]  # X-Achse
        self.positions_row = ["A", "B", "C", "D"]  # Y-Achse
        self.total_stations = len(self.positions_row) * len(self.positions_column)

        # Haupt-Variablen
        self.ser = None  # Serielle Verbindung (wird in init_serial() geöffnet)
        self.picam = None  # Kameraobjekt (Picamera2)

        # Workflow-Status
        self.run_dir = (
            None  # Aktueller Haupt-Ordner (z. B. /home/pi/images/run_20230224_103456)
        )
        self.current_pass_dir = None  # Aktueller Unterordner (pass_01, pass_02, etc.)
        self.pass_count = 0  # Aktuelle Wiederholung (1..repeats)
        self.repeats = 0  # Gelesen aus GUI
        self.move_count = 0  # Wie viele Stationen im aktuellen Pass durchlaufen?

        # 1) Zuerst GUI-Elemente erstellen
        self.create_widgets()

        # 2) Dann Kamera initialisieren (log_message() braucht schon log_text!)
        self.init_camera()

        # 3) Zum Schluss Polling für Arduino starten
        self.poll_arduino()

    # BEENDEN
    def on_closing(self):
        """Wird aufgerufen, wenn das Fenster geschlossen wird."""
        self.log_message("Beende Anwendung...")
        if self.picam:
            self.picam.stop()
            self.picam.close()
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.destroy()

    def run(self):
        """
        Startet die Tkinter-Hauptschleife.
        Anstatt mainloop() direkt im if __name__ ..., hier gekapselt.
        """
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()

    def create_widgets(self):
        """Erstellt alle Tkinter-Widgets und legt das Layout fest."""
        # Spaltenanpassung
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Wiederholungen: [<] [Textfeld] [>]
        repeats_frame = ttk.Frame(self)
        repeats_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        tk.Label(repeats_frame, text="Wiederholungen:", anchor="e").grid(
            row=0, column=0, padx=5
        )
        self.repeats_var = tk.IntVar(value=2)
        minus_repeats = ttk.Button(
            repeats_frame, text="<", command=self.decrement_repeats, width=3
        )
        minus_repeats.grid(row=0, column=1, padx=5, ipadx=10, ipady=10)
        repeats_entry = ttk.Entry(
            repeats_frame,
            textvariable=self.repeats_var,
            width=5,
            font=("Helvetica", 16),
            justify="center",
        )
        repeats_entry.grid(row=0, column=2, padx=5)
        plus_repeats = ttk.Button(
            repeats_frame, text=">", command=self.increment_repeats, width=3
        )
        plus_repeats.grid(row=0, column=3, padx=5, ipadx=10, ipady=10)

        # Pause (in Minuten): [<] [Textfeld] [>]
        pause_frame = ttk.Frame(self)
        pause_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        tk.Label(pause_frame, text="Pause (Minuten):", anchor="e").grid(
            row=0, column=0, padx=5
        )
        self.pause_var = tk.IntVar(value=1)
        minus_pause = ttk.Button(
            pause_frame, text="<", command=self.decrement_pause, width=3
        )
        minus_pause.grid(row=0, column=1, padx=5, ipadx=10, ipady=10)
        pause_entry = ttk.Entry(
            pause_frame,
            textvariable=self.pause_var,
            width=5,
            font=("Helvetica", 16),
            justify="center",
        )
        pause_entry.grid(row=0, column=2, padx=5)
        plus_pause = ttk.Button(
            pause_frame, text=">", command=self.increment_pause, width=3
        )
        plus_pause.grid(row=0, column=3, padx=5, ipadx=10, ipady=10)

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
            button_frame1, text="Manueller NEXT", command=self.on_manual_next, width=22
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
            command=self.manual_take_photo,
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

    # LOGGING
    def log_message(self, msg):
        """
        Loggt die Nachricht mit Zeitstempel über den Logger (für Logdateien)
        und zeigt sie gleichzeitig im GUI-Text-Widget an.
        """
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        # Logge über den Logger (zum Beispiel in protocol.log oder error.log)
        if hasattr(self, "logger"):
            self.logger.info(line)
        # Zeige die Nachricht im GUI an
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        # Auch in der Konsole ausgeben
        print(line)

    # AUTOMATIKLÄUFE
    def on_start_program(self):
        """
        Wird aufgerufen, wenn "Programm START" geklickt wird.
        1) Legt einen neuen Hauptordner an.
        2) Liest repeats aus GUI.
        3) Legt den ersten Pass-Unterordner an.
        4) Schickt 'START' an Arduino.
        """
        now_str = time.strftime("run_%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(BASE_OUTPUT_DIR, now_str)
        os.makedirs(self.run_dir, exist_ok=True)
        self.log_message(f"Neuer Lauf-Ordner: {self.run_dir}")

        repeats = self.repeats_var.get()
        if repeats < 1:
            self.log_message("Bitte eine Zahl größer als 0 für Wiederholungen eingeben.")
            return
        self.repeats = repeats

        # Pass 1 beginnen
        self.pass_count = 1
        self.move_count = 0
        self.start_pass_folder()

        self.log_message("Sende 'START' an Arduino...")
        self.send_message("START")

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

    def take_photo_for_pass(self):
        """
        Ermittelt aus move_count die (row, column), speichert Foto.
        Bsp-Dateiname: well_B3_pass1_20230315_101122.jpg
        """
        if not self.picam:
            self.log_message("Kamera nicht vorhanden.")
            return

        col_index = self.move_count % len(self.positions_column)
        row_index = self.move_count // len(self.positions_column)
        col_value = self.positions_column[col_index]
        row_value = self.positions_row[row_index]

        # => Dateiname
        # pass_count fängt bei 1 an, also pass1, pass2, ...
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"well_{row_value}{col_value}_pass{self.pass_count}_{timestamp}.jpg"

        # => Ablage im aktuellen pass_XX-Ordner
        filepath = os.path.join(self.current_pass_dir, filename)

        try:
            self.picam.capture_file(filepath)
            self.log_message(f"Foto aufgenommen: {filepath}")
        except Exception as e:
            self.log_message(f"Fehler bei Fotoaufnahme: {e}")

    # MANUELLES NEXT
    def on_manual_next(self):
        """
        Button-Callback: Sendet 'NEXT' manuell an den Arduino,
        damit er eine Station weiterfährt.
        """
        self.log_message("Sende 'NEXT' (manuell).")
        self.send_message("NEXT")

    # MANUELL FOTO AUFNEHMEN
    def manual_take_photo(self):
        """Wird per Button-Klick ausgelöst, um ein manuelles Foto in einem tagesbasierten Ordner zu speichern."""
        if not self.picam:
            self.log_message("Kamera nicht vorhanden.")
            return

        # Bestimme das Zielverzeichnis basierend auf dem heutigen Datum (z. B. manual_20230315)
        today_str = time.strftime("manual_%Y%m%d")
        manual_dir = os.path.join(BASE_OUTPUT_DIR, today_str)
        os.makedirs(manual_dir, exist_ok=True)

        # Erzeuge einen Dateinamen für das Bild
        filename = time.strftime("manual_%Y%m%d_%H%M%S.jpg")
        filepath = os.path.join(manual_dir, filename)

        try:
            self.picam.capture_file(filepath)
            self.log_message(f"MANUELLES Foto aufgenommen: {filepath}")
        except Exception as e:
            self.log_message(f"Fehler bei manuellem Foto: {e}")

    # GENERIEREN & HOCHLADEN
    def on_generate_and_upload(self):
        """Button-Klick: Erstellt config.h, kompiliert und lädt den Sketch hoch."""
        repeats = self.repeats_var.get()
        pause_ms = self.pause_var.get()

        if repeats < 1:
            self.log_message(
                "Bitte eine Zahl größer als 0 für Wiederholungen eingeben."
            )
            return
        if pause_ms < 1:
            self.log_message(
                "Bitte eine Zahl größer als 0 für Pause (Minuten) eingeben."
            )
            return

        repeats = int(repeats)
        pause_mins = int(pause_ms)

        # 1) config.h generieren
        self.log_message("Generiere config.h...")
        self.generate_config_file(repeats, pause_mins)

        # 2) Kompilieren
        self.log_message("Kompiliere Sketch...")
        self.compile_sketch()

        # 3) Hochladen
        self.log_message("Lade hoch...")
        self.upload_sketch()

        self.log_message("Fertig!")

    def generate_config_file(self, repeats, pause_minutes):
        """Ersetzt Platzhalter in config_template.h und speichert als config.h."""
        try:
            with open(TEMPLATE_FILE, "r") as template:
                content = template.read()
            pause_ms = pause_minutes * 60000
            content = content.replace("{{REPEATS_PLACEHOLDER}}", str(repeats))
            content = content.replace("{{PAUSE_PLACEHOLDER}}", str(pause_ms))
            with open(CONFIG_FILE, "w") as config:
                config.write(content)
            self.log_message("config.h wurde erfolgreich generiert.")
        except FileNotFoundError:
            self.log_message(f"FEHLER: {TEMPLATE_FILE} nicht gefunden.")

    def compile_sketch(self):
        """Ruft arduino-cli compile auf."""
        try:
            subprocess.run(
                [ARDUINO_CLI_PATH, "compile", "--fqbn", FQBN, "."], check=True
            )
            self.log_message("Kompilierung erfolgreich.")
        except subprocess.CalledProcessError as e:
            self.log_message(f"Fehler bei der Kompilierung: {e}")

    def upload_sketch(self):
        """Ruft arduino-cli upload auf."""
        try:
            subprocess.run(
                [ARDUINO_CLI_PATH, "upload", "-p", SERIAL_PORT, "--fqbn", FQBN, "."],
                check=True,
            )
            self.log_message("Upload erfolgreich.")
        except subprocess.CalledProcessError as e:
            self.log_message(f"Fehler beim Upload: {e}")

    # ABBRECHEN
    def on_abort(self):
        """Button-Klick: Sende 'ABORT' an Arduino, der daraufhin abbrechen soll."""
        self.log_message("Sende 'ABORT' an Arduino...")
        self.send_message("ABORT")


def main():
    app = Paparazzo()
    app.run()


# STARTPUNKT
if __name__ == "__main__":
    main()
