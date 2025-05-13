#!/usr/bin/env python3

import datetime
import os
import tkinter as tk
from tkinter import Toplevel, ttk

import pkg_resources

from packages.camera_serial_manager import CameraSerialManager
from packages.logger import (log_message, logging, set_gui_instance,
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

        set_gui_instance(self)
        self.logger = setup_logging()

        # log_text zuerst erstellen, um log Fehler zu vermeiden
        self.log_text = tk.Text(self, wrap="word", height=17, width=30)
        self.log_text.grid(row=5, column=0, columnspan=4, padx=10, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=5, column=4, padx=(0, 10), sticky="ns")
        self.log_text["yscrollcommand"] = scrollbar.set

        # Spaltenkonfiguration
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=0)

        self.create_widgets()

        # CameraSerialManager EINMAL initialisieren!
        self.manager = CameraSerialManager(gui=self)

        # GUI Titel und Style setzen
        version = get_version()
        self.title(f"Paparazzo v{version}")

        # Style Options
        style = ttk.Style()
        style.theme_use("clam")  # 'clam', 'alt', 'default', 'classic'
        style.configure("CenterEntry.TEntry", padding=(0, 10, 0, 10))
        style.configure("Custom.Vertical.TScrollbar", width=20)

        # Fenster maximiert starten
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+0+0")

        log_message("Starte Paparazzo GUI...", "info")
        log_message("Initialisiere Log System...", "info")

    # Methode zum Abfragen der Werte:
    def get_repeats(self):
        return self.repeats_var.get()

    def get_pause_minutes(self):
        return self.pause_var.get()

    # Counter Value Management
    def increment_move_count(self):
        self.MOVE_COUNT += 1

    def reset_move_count(self):
        self.MOVE_COUNT = 0

    def increment_cycle_count(self):
        self.CYCLE_COUNT += 1

    def reset_cycle_count(self):
        self.CYCLE_COUNT = 0

    def get_current_move_count(self):
        return self.MOVE_COUNT

    def get_current_cycle_count(self):
        return self.CYCLE_COUNT

    # GUI aufbauen
    def create_widgets(self):
        """Erstellt alle Tkinter-Widgets und legt das Layout fest."""
        # LAYOUT
        button_width = 14
        font_size = 22
        # Wiederholungen: [<] [Textfeld] [>]
        config_frame = ttk.Frame(self)
        config_frame.grid(row=0, rowspan=2, column=0, sticky="ew")

        # Standardwert im Eingabefeld
        self.repeats_var = tk.IntVar(value=2)

        # Wiederholungen Eingabefeld
        config_entry = ttk.Entry(
            config_frame,
            textvariable=self.repeats_var,
            width=5,
            font=("Helvetica", font_size),
            justify="center",
            style="CenterEntry.TEntry",
        )
        config_entry.grid(row=0, column=0, padx=10)

        # Knopf Wiederholungen
        config_repeats = ttk.Button(
            config_frame,
            text="Wiederholungen",
            command=self.open_repeats_popup,
            width=button_width,
        )
        config_repeats.grid(row=0, column=1, padx=10, pady=10, ipadx=12, ipady=12)

        # Wert im Pause Eingabefeld
        self.pause_var = tk.IntVar(value=1)

        # Textfeld Pause
        config_entry = ttk.Entry(
            config_frame,
            textvariable=self.pause_var,
            width=5,
            font=("Helvetica", 22),
            justify="center",
            style="CenterEntry.TEntry",
        )
        config_entry.grid(row=1, column=0, padx=10)

        # Eingabeknopf Pause
        config_pause = ttk.Button(
            config_frame,
            text="Pause [min]",
            command=self.open_pause_popup,
            width=button_width,
        )
        config_pause.grid(row=1, column=1, padx=10, pady=10, ipadx=12, ipady=12)

        # Execution Elements
        execution_frame = ttk.Frame(self)
        execution_frame.grid(row=0, rowspan=2, column=1, sticky="ew")

        # Generieren & Hochladen
        gen_upload_btn = ttk.Button(
            execution_frame,
            text="Programm laden",
            command=self.on_configure,
            width=button_width,
        )
        gen_upload_btn.grid(row=0, column=0, padx=10, pady=10, ipadx=12, ipady=12)

        # Manuellzugriff
        position_button = ttk.Button(
            execution_frame,
            text="Manuelle Steuerung",
            command=self.on_open_manual_position_popup,
            width=button_width,
        )
        position_button.grid(row=1, column=0, padx=10, pady=10, ipadx=12, ipady=12)

        # Run Options Elements
        runoptions_frame = ttk.Frame(self)
        runoptions_frame.grid(row=0, rowspan=2, column=2, sticky="ew")

        # Programm START
        start_btn = ttk.Button(
            runoptions_frame,
            text="Starten",
            command=self.on_start_program,
            width=button_width,
        )
        start_btn.grid(row=0, column=0, padx=10, pady=10, ipadx=12, ipady=12)

        # Abbrechen
        abort_btn = ttk.Button(
            runoptions_frame,
            text="Abbrechen",
            command=self.on_abort,
            width=button_width,
        )
        abort_btn.grid(row=1, column=0, padx=10, pady=10, ipadx=12, ipady=12)

        # System Elements
        system_frame = ttk.Frame(self)
        system_frame.grid(row=0, rowspan=2, column=3, sticky="ew")

        # Schließen
        close_button = ttk.Button(
            system_frame, text="Schließen", command=self.on_close, width=button_width
        )
        close_button.grid(row=0, column=0, padx=10, pady=10, ipadx=12, ipady=12)

    # =============================================
    # Popup Elemente
    # =============================================

    # Konfigurationseingaben
    def open_repeats_popup(self):
        self.open_numpad_popup(self.repeats_var, "Wiederholungen")

    def open_pause_popup(self):
        self.open_numpad_popup(self.pause_var, "Pause [min]")

    # Numpad Aktionen
    def open_numpad_popup(self, variable: tk.IntVar, title: str):
        popup = tk.Toplevel(self)
        popup.title(title)

        temp_var = tk.StringVar(value=str(variable.get()))
        entry = ttk.Entry(
            popup, textvariable=temp_var, font=("Helvetica", 25), justify="center"
        )
        entry.grid(row=0, column=0, columnspan=3, pady=10)

        def confirm():
            val = temp_var.get()
            if val.isdigit() and int(val) > 0:
                variable.set(int(val))
                log_message(f"{title} gesetzt auf {val}", "info")
                popup.destroy()
            else:
                log_message(f"Ungültige Eingabe für {title}!", "error")

        # Numpad (Ziffern 1–9)
        digits = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        for idx, digit in enumerate(digits):
            btn = ttk.Button(
                popup,
                text=str(digit),
                command=lambda d=digit: temp_var.set(temp_var.get() + str(d)),
            )
            btn.grid(
                row=(idx // 3) + 1, column=(idx % 3), padx=5, pady=5, ipadx=10, ipady=10
            )

        # Letzte Reihe mit C - 0 - OK
        clear_btn = ttk.Button(popup, text="C", command=lambda: temp_var.set(""))
        clear_btn.grid(row=4, column=0, padx=5, pady=5, ipadx=10, ipady=10)

        zero_btn = ttk.Button(
            popup, text="0", command=lambda: temp_var.set(temp_var.get() + "0")
        )
        zero_btn.grid(row=4, column=1, padx=5, pady=5, ipadx=10, ipady=10)

        ok_btn = ttk.Button(popup, text="OK", command=confirm)
        ok_btn.grid(row=4, column=2, padx=5, pady=5, ipadx=10, ipady=10)

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

        self.manager.reset_cycle_count()
        self.manager.reset_move_count()

        self.manager.setup_run_directory()
        self.manager.setup_cycle_directory()

        log_message("Sende 'START' an Arduino...", "info")
        self.manager.send_command("START")

        self.manager.start_polling()

    # Abbrechen
    def on_abort(self):
        """Button-Klick: Sende 'ABORT' an Arduino, der daraufhin abbrechen soll."""
        log_message("Sende 'ABORT' an Arduino...", "info")
        self.manager.send_command("ABORT")
        self.manager.stop_polling()

    # Manuelles Positionieren
    def manual_move_to_position(self, row, col):
        command = f"MOVE_{row}{col}"
        self.manager.send_command(command)

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

        dir_path = f"images/manual_{date_str}/"
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f"{time_str}_{row_value}{col_value}.jpg")

        self.manager.take_photo()

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
    def cleanup(self):
        # Hier alle wichtigen Vorgänge beenden:
        log_message("Bereinige laufende Vorgänge...")

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

    def on_close(self):
        try:
            self.cleanup()
        except Exception as e:
            print("Fehler beim Herunterfahren:", e)
        finally:
            # 4️⃣ Tkinter-Fenster sauber schließen
            log_message("GUI wird zerstört...", "info")
            set_gui_instance(None)
            logging.shutdown()  # Schließt den Logger sauber
            self.destroy()


def main():
    app = Paparazzo()
    app.mainloop()


if __name__ == "__main__":
    main()
