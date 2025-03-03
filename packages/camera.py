#!/usr/bin/env python3

import os
import time

from picamera2 import Picamera2  # , Preview

from .config import (BASE_OUTPUT_DIR)
from .logger import log_message

picam = None  # Global definieren


# KAMERA INITIIEREN
def init_camera():
    global picam
    log_message("Starte init_camera...")
    try:
        picam = Picamera2()
        picam.configure(picam.create_still_configuration())
        picam.start_preview()  # Preview.QTGL
        picam.start()
        time.sleep(1)  # Kleine Wartezeit, bis alles bereit ist
        log_message("Kamera initialisiert.")
    except Exception as e:
        log_message(f"Kamera-Fehler: {e}")
        picam = None  # Falls Kamera nicht initialisiert werden kann


# MANUELL FOTO AUFNEHMEN
def manual_take_photo():
    """Wird per Button-Klick ausgelöst, um ein manuelles Foto in einem tagesbasierten Ordner zu speichern."""
    if not picam:
        log_message("Kamera nicht vorhanden.")
        return

    # Bestimme das Zielverzeichnis basierend auf dem heutigen Datum (z. B. manual_20230315)
    today_str = time.strftime("manual_%Y%m%d")
    manual_dir = os.path.join(BASE_OUTPUT_DIR, today_str)
    os.makedirs(manual_dir, exist_ok=True)

    # Erzeuge einen Dateinamen für das Bild
    filename = time.strftime("manual_%Y%m%d_%H%M%S.jpg")
    filepath = os.path.join(manual_dir, filename)

    try:
        picam.capture_file(filepath)
        log_message(f"MANUELLES Foto aufgenommen: {filepath}")
    except Exception as e:
        log_message(f"Fehler bei manuellem Foto: {e}")
