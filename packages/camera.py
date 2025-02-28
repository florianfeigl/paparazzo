# KAMERA
import time

from picamera2 import Picamera2, Preview


def init_camera(self):
    self.log_message("Starte init_camera...")
    try:
        self.picam = Picamera2()
        # Konfiguriere die Kamera für Standbilder
        self.picam.configure(self.picam.create_still_configuration())
        # (Optional) Starte einen Preview (NULL/DRM/QTGL)
        self.picam.start_preview(Preview.NULL)
        # Starte die Kamera
        self.picam.start()
        time.sleep(1)  # Kleine Wartezeit, bis alles bereit ist
        self.log_message("Kamera initialisiert.")
    except Exception as e:
        self.log_message(f"Kamera-Fehler: {e}")
        self.picam = None
