import datetime
import logging
import os
import time

BASE_OUTPUT_DIR = "/home/pi/images"

# Logger-Setup für globalen Zugriff
logger = None


def setup_logging():
    """
    Richtet zwei Logger-Handler ein:
      - Einen für alle Logeinträge (Protokoll)
      - Einen für Fehler (Error)
    Die Dateinamen enthalten den aktuellen Zeitstempel.
    """
    global logger
    if logger is not None:
        return logger  # Falls der Logger schon existiert

    now_str = time.strftime("run_%Y%m%d_%H%M%S")
    protocol_filename = os.path.join(BASE_OUTPUT_DIR, f"protocol_{now_str}.log")
    error_filename = os.path.join(BASE_OUTPUT_DIR, f"error_{now_str}.log")

    logger = logging.getLogger("Paparazzo")
    logger.setLevel(logging.DEBUG)  # Alle Nachrichten sollen verarbeitet werden

    # FileHandler für das Protokoll (alle Loglevels ab DEBUG/INFO)
    ph = logging.FileHandler(protocol_filename)
    ph.setLevel(logging.DEBUG)
    # FileHandler für Fehler (nur ERROR und höher)
    eh = logging.FileHandler(error_filename)
    eh.setLevel(logging.ERROR)

    # Formatter definieren (Zeitstempel, Level und Nachricht)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    ph.setFormatter(formatter)
    eh.setFormatter(formatter)

    # Handler zum Logger hinzufügen
    logger.addHandler(ph)
    logger.addHandler(eh)
    return logger


def log_message(msg, level="info"):
    """
    Schreibt Nachrichten ins Log und in die Konsole.

    Args:
        msg (str): Die Nachricht, die geloggt werden soll.
        level (str): Das Logging-Level ('info', 'warning', 'error', 'debug').
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{ts}] {msg}"

    # In die Konsole ausgeben
    print(log_entry)

    # Falls der Logger nicht existiert, erstelle ihn
    global logger
    if logger is None:
        logger = setup_logging()

    # In das Log-File schreiben
    log_levels = {
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error,
        "debug": logger.debug,
    }
    log_func = log_levels.get(level, logger.info)
    log_func(msg)
