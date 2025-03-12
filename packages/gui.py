#!/usr/bin/env python3

import datetime
import os
import tkinter as tk
from tkinter import Toplevel, ttk

import pkg_resources

from packages.camera_serial_manager import CameraSerialManager
from packages.logger import (gui_instance, log_message, set_gui_instance,
                             setup_logging)

# Logger zuweisen
logger = setup_logging()


def get_version():
    try:
        return pkg_resources.get_distribution("paparazzo").version
    except pkg_resources.DistributionNotFound:
        return "Unknown"


class Paparazzo(tk.Tk):
    """
    Hauptklasse für die Tkinter-GUI.
    """

    picam = None

    def __init__(self):
        super().__init__()
        global gui_instance

        # GUI Titel
        version = get_version()
        self.title(f"Paparazzo v{version}")

        # GUI Darstellung
        style = ttk.Style()
        style.theme_use("clam")  # Alternativ: 'alt', 'default', 'classic'
        style.configure("CenterEntry.TEntry", padding=(0, 10, 0, 10))
        style.configure("Repeats.TFrame", background="lightgreen")
        style.configure("Pause.TFrame", background="yellow")

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

        # Initialisiert und konfiguriert Kamera
        self.manager = CameraSerialManager()

        # Polling für Arduino starten
        self.after(100, self.manager.start_polling)

    # GUI aufbauen
    def create_widgets(self):
        """Erstellt alle Tkinter-Widgets und legt das Layout fest."""
        # Spaltenanpassung
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        # LAYOUT
        # Wiederholungen: [<] [Textfeld] [>]
        repeats_frame = ttk.Frame(self, style="Repeats.TFrame")
        repeats_frame.grid(row=0, column=0)

        # Standardwert im Eingabefeld
        self.repeats_var = tk.IntVar(value=2)

        # Wiederholungen Minusbutton
        minus_repeats = ttk.Button(
            repeats_frame, text="<", command=self.decrement_repeats, width=7
        )
        minus_repeats.grid(row=0, column=0, padx=10, pady=10, ipadx=14, ipady=14)

        # Wiederholungen Eingabefeld
        repeats_entry = ttk.Entry(
            repeats_frame,
            textvariable=self.repeats_var,
            width=3,
            font=("Helvetica", 25),
            justify="center",
            style="CenterEntry.TEntry",
        )

        # Eingabefeld Wiederholungen
        repeats_entry.grid(row=0, column=1, sticky="ew")

        # Plusknopf Wiederholungen
        plus_repeats = ttk.Button(
            repeats_frame, text=">", command=self.increment_repeats, width=7
        )
        plus_repeats.grid(row=0, column=2, padx=10, pady=10, ipadx=14, ipady=14)

        # LABEL FRAME
        label_frame = ttk.Frame(self)
        label_frame.columnconfigure(0, weight=1)
        label_frame.columnconfigure(1, weight=1)
        label_frame.columnconfigure(2, weight=1)
        label_frame.grid(row=1, column=0, sticky="ew")

        # Wiederholungen Label
        tk.Label(
            label_frame,
            text="Wiederholungen",
            background="lightgreen",
            font=("Helvetica", 10, "bold"),
        ).grid(row=0, column=0, ipadx=10, ipady=10)

        # Platzhalterzelle in Zeile 0, Spalte 1 (keine Widgets hier)
        tk.Label(label_frame, text="").grid(row=0, column=1, sticky="ew")

        # Pausenlabel
        tk.Label(
            label_frame,
            text="Pause [min]",
            background="yellow",
            font=("Helvetica", 10, "bold"),
        ).grid(row=0, column=2, ipadx=10, ipady=10)
        # Pause (in Minuten): [<] [Textfeld] [>]
        pause_frame = ttk.Frame(self, style="Pause.TFrame")
        pause_frame.grid(row=2, column=0)

        # Wert im Pause Eingabefeld
        self.pause_var = tk.IntVar(value=1)

        # Minusbutton Pause
        minus_pause = ttk.Button(
            pause_frame, text="<", command=self.decrement_pause, width=7
        )
        minus_pause.grid(row=0, column=0, padx=10, pady=10, ipadx=14, ipady=14)

        # Eingabefeld Pause
        pause_entry = ttk.Entry(
            pause_frame,
            textvariable=self.pause_var,
            width=3,
            font=("Helvetica", 24),
            justify="center",
            style="CenterEntry.TEntry",
        )
        pause_entry.grid(row=0, column=1)

        # Plusknopf Pause
        plus_pause = ttk.Button(
            pause_frame, text=">", command=self.increment_pause, width=7
        )
        plus_pause.grid(row=0, column=2, padx=10, ipadx=14, ipady=14)

        # Execution Elements
        execution_frame = ttk.Frame(self)
        execution_frame.grid(row=0, rowspan=3, column=1)

        # Generieren & Hochladen
        gen_upload_btn = ttk.Button(
            execution_frame,
            text="Konfigurieren",
            command=self.on_configure,
            width=16,
        )
        gen_upload_btn.grid(row=0, column=1, padx=10, ipadx=12, ipady=12)

        # Programm START
        start_btn = ttk.Button(
            execution_frame,
            text="Starten",
            command=self.on_start_program,
            width=16,
        )
        start_btn.grid(row=1, column=1, padx=10, pady=10, ipadx=12, ipady=12)

        # Abbrechen
        abort_btn = ttk.Button(
            execution_frame, text="Abbrechen", command=self.on_abort, width=16
        )
        abort_btn.grid(row=2, column=1, padx=10, ipadx=14, ipady=14)

        # System Elements
        administration_frame = ttk.Frame(self)
        administration_frame.grid(row=0, rowspan=3, column=2)

        # Positionieren
        position_button = ttk.Button(
            administration_frame,
            text="Positionieren",
            command=self.on_open_manual_position_popup,
            width=16,
        )
        position_button.grid(row=0, column=2, padx=10, ipadx=12, ipady=12)

        # Fotografieren
        photo_button = ttk.Button(
            administration_frame,
            text="Fotografieren",
            command=self.on_take_photo,
            width=16,
        )
        photo_button.grid(row=1, column=2, padx=10, pady=10, ipadx=12, ipady=12)

        # Schließen
        close_button = ttk.Button(
            administration_frame, text="Schließen", command=self.on_close, width=16
        )
        close_button.grid(row=2, column=2, padx=10, ipadx=12, ipady=12)

        # Log-Text-Widget initialisieren
        self.log_text = tk.Text(self, wrap="word", height=14, width=20)
        self.log_text.grid(row=5, column=0, columnspan=3, padx=(10, 0), sticky="ew")

        # Scrollbar für das Log-Text-Widget
        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=5, column=3, sticky="ns")
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

    # Konfigurieren
    def on_configure(self):
        """Button-Klick: Erstellt config.h, kompiliert und lädt den Sketch hoch."""
        log_message("Starte Konfiguration...", "info")
        success = self.prepare_and_upload_sketch()

        if success:
            log_message("Fertig!", "info")
        else:
            log_message("Konfiguration fehlgeschlagen!", "error")

    # Sketch vorbereiten und laden 
    def prepare_and_upload_sketch(self):
        """Generiert config.h, kompiliert und lädt den Sketch hoch."""
        REPEATS = self.repeats_var.get()
        PAUSE = self.pause_var.get()
        PAUSE_MS = PAUSE * 60000

        if REPEATS < 1:
            log_message(
                "Unzulässige Eingabe. Bitte eine Zahl größer als 0 für Wiederholungen eingeben.",
                "error",
            )
            return False  # signalisiert Fehlschlag

        if PAUSE_MS < 60000:
            log_message(
                "Unzulässige Eingabe. Bitte eine Zahl größer als 1 Minute für Pause eingeben.",
                "error",
            )
            return False  # signalisiert Fehlschlag

        self.manager.generate_config_file(REPEATS, PAUSE_MS)
        self.manager.compile_sketch()
        self.manager.upload_sketch()

        log_message("Konfiguration abgeschlossen!", "info")
        return True  # signalisiert Erfolg

    # Starten
    def on_start_program(self):
        if not self.prepare_and_upload_sketch():
            log_message("Programmstart abgebrochen.", "error")
            return

        self.manager.reset_pass_count()
        self.manager.reset_move_count()

        self.manager.setup_run_directory()
        self.manager.setup_pass_directory()

        log_message("Sende 'START' an Arduino...", "info")
        self.manager.send_command("START")

    # Abbrechen
    def on_abort(self):
        """Button-Klick: Sende 'ABORT' an Arduino, der daraufhin abbrechen soll."""
        log_message("Sende 'ABORT' an Arduino...", "info")
        self.manager.send_command("ABORT")

    # Manuelles Positionieren
    def manual_move_to_position(self, row, col):
        print(f"Moving to position {row}{col}")
        # Hier Steuerungsbefehl für die Bewegung einfügen

    def on_open_manual_position_popup(self):
        popup = Toplevel(self)
        popup.title("Manuelle Position wählen")

        # Manuelle Positions-Buttons
        for row in "ABCD":
            for col in range(1, 7):
                btn = tk.Button(
                    popup,
                    text=f"{row}{col}",
                    command=lambda r=row, c=col: self.manual_move_to_position(r, c),
                )
                btn.grid(row=ord(row) - ord("A"), column=col - 1, padx=5, pady=5)

        # Fotografieren-Button
        shoot_btn = tk.Button(popup, text="Fotografieren", command=self.on_take_photo)
        shoot_btn.grid(row=4, column=0, columnspan=6, padx=5, pady=10, sticky="ew")

        # Fenster schließen-Button
        close_btn = tk.Button(
            popup, text="Fenster schließen", command=lambda: self.on_close_popup(popup)
        )
        close_btn.grid(row=5, column=0, columnspan=6, padx=5, pady=10, sticky="ew")

    # Fotografieren
    def on_take_photo(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%Y%m%d_%H%M%S")

        row_value, col_value = "X", "X"  # Hier Werte von der aktuellen Position holen

        dir_path = f"Paparazzo/images/manual_{date_str}/"
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(
            dir_path, f"{time_str}_{row_value}{col_value}_manual_shot.jpg"
        )

        print(f"Foto gespeichert unter: {file_path}")
        # Hier Kamera-Befehl zum Speichern des Bildes einfügen

    # Popup Schließen
    def on_close_popup(self, popup):
        if self.manager.picam is not None:
            self.manager.picam.stop()
            self.manager.picam.close()
            self.manager.picam = None
        popup.destroy()

    # Programm Schließen
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


def main():
    app = Paparazzo()
    app.mainloop()


if __name__ == "__main__":
    main()
