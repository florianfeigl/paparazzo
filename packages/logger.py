#!/usr/bin/env python3

import logging
import os
import time

from packages.config import LOGS_DIR

# Globale Variable für GUI-Referenz
gui_instance = None
logger = None  # Globale Logger-Variable


class TextWidgetHandler(logging.Handler):
    """
    Leitet alle Log-Ausgaben ins Text-Widget (falls es existiert).
    Falls das GUI noch nicht läuft, werden die Meldungen auf der Konsole ausgegeben.
    """

    def emit(self, record):
        msg = self.format(record)
        if (
            gui_instance
            and hasattr(gui_instance, "log_text")
            and gui_instance.log_text.winfo_exists()
        ):
            gui_instance.log_text.insert("end", msg + "\n")
            gui_instance.log_text.see("end")
            gui_instance.after(100, gui_instance.log_text.update_idletasks)
        else:
            # Falls keine GUI vorhanden ist, sende an das Terminal
            print(msg)


def setup_logging():
    """
    Richtet den Hauptlogger "Paparazzo" ein, der alle Meldungen gleichzeitig
      - in ein Protokoll-Logfile (ab INFO)
      - in ein Error-Logfile (ab ERROR)
      - in die GUI (über den TextWidgetHandler, ab DEBUG)
    schreibt.
    Gibt am Ende den konfigurierten Logger zurück.
    """
    global logger  # Greife auf die globale Logger-Variable zu

    if logger is not None:
        return logger  # Falls der Logger schon existiert, einfach zurückgeben

    # Haupt-Logger erstellen
    logger = logging.getLogger("Paparazzo")
    logger.setLevel(logging.DEBUG)  # Erfasst alle Meldungen ab DEBUG

    # Damit wir keine doppelten Handler bekommen
    for h in list(logger.handlers):
        logger.removeHandler(h)

    # Log-Dateinamen setzen: Protokoll & Error
    now_str = time.strftime("run_%Y%m%d_%H%M%S")
    protocol_filename = os.path.join(LOGS_DIR, f"protocol_{now_str}.log")
    error_filename = os.path.join(LOGS_DIR, f"error_{now_str}.log")

    # 1) FileHandler für alle Meldungen (INFO und höher)
    fh = logging.FileHandler(protocol_filename)
    fh.setLevel(logging.INFO)

    # 2) FileHandler für Fehler (ERROR und höher)
    eh = logging.FileHandler(error_filename)
    eh.setLevel(logging.ERROR)

    # 3) Handler für das GUI-Text-Widget
    th = TextWidgetHandler()
    th.setLevel(logging.DEBUG)  # Zeigt alles ab DEBUG auch in der GUI an

    # Einen Formatter definieren, damit wir Datum/Zeit/Level dabei haben
    fmt = "[%(asctime)s] %(levelname)s: %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # Formatter den Handlern zuweisen
    fh.setFormatter(formatter)
    eh.setFormatter(formatter)
    th.setFormatter(formatter)

    # Handler beim Logger anhängen
    logger.addHandler(fh)
    logger.addHandler(eh)
    logger.addHandler(th)

    return logger


def set_gui_instance(gui):
    """Setzt die GUI-Instanz, um Logs im Tkinter-Text-Widget anzuzeigen."""
    global gui_instance
    gui_instance = gui


def log_message(msg, level="info"):
    """
    Loggt eine Nachricht auf verschiedenen Ebenen und gibt sie in die GUI aus.
    """
    global logger

    if logger is None:
        logger = setup_logging()  # Stelle sicher, dass der Logger initialisiert ist

    # Logging-Level festlegen
    log_levels = {
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error,
        "debug": logger.debug,
    }
    log_func = log_levels.get(level, logger.info)

    # Log-Nachricht schreiben
    log_func(msg)
