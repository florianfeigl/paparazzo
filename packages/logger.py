import logging
import os
import time

BASE_OUTPUT_DIR = "/home/pi/images"

def setup_logging():
    """
    Richtet zwei Logger-Handler ein:
      - Einen für alle Logeinträge (Protokoll)
      - Einen für Fehler (Error)
    Die Dateinamen enthalten den aktuellen Zeitstempel.
    """
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
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    ph.setFormatter(formatter)
    eh.setFormatter(formatter)

    # Handler zum Logger hinzufügen
    logger.addHandler(ph)
    logger.addHandler(eh)
    return logger
