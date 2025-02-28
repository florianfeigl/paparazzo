# SERIELLE KOMMUNIKATION
import time

import serial

from .config import BAUD_RATE, SERIAL_PORT


def init_serial(self):
    """Öffnet den seriellen Port, wenn noch nicht geschehen."""
    if self.ser is None:
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            time.sleep(2)  # Arduino-Reset abwarten
            self.log_message(f"Serieller Port {SERIAL_PORT} geöffnet.")
        except serial.SerialException as e:
            self.log_message(f"ERROR: Could not open serial port: {e}")


def send_message(self, message):
    """Sendet ein Kommando an den Arduino (z. B. 'START', 'NEXT', 'ABORT')."""
    self.init_serial()
    if self.ser and self.ser.is_open:
        self.ser.write((message + "\n").encode("utf-8"))
        self.ser.flush()
        self.log_message(f"=> Arduino: {message}")


def read_arduino_line(self):
    """
    Liest eine Zeile aus der seriellen Verbindung.
    Entfernt < > - falls das Protokoll so formatiert ist.
    """
    self.init_serial()
    if not (self.ser and self.ser.is_open):
        return None

    raw_line = self.ser.readline().decode("utf-8", errors="ignore").strip()
    if raw_line:
        if raw_line.startswith("<") and raw_line.endswith(">"):
            return raw_line[1:-1]
        return raw_line
    return None


def poll_arduino(self):
    line = self.read_arduino_line()
    if line:
        self.log_message(f"Arduino: {line}")
        if line == "MOVE_COMPLETED":
            # => Foto machen
            self.take_photo_for_pass()
            # => Station weiterzählen
            self.move_count += 1

            # => Wenn noch nicht alle Stationen in diesem Pass fertig:
            if self.move_count < self.total_stations:
                self.send_message("NEXT")
            else:
                self.log_message(f"Pass {self.pass_count} abgeschlossen.")
                if self.pass_count < self.repeats:
                    self.start_next_pass()
                else:
                    self.log_message("ALLE Wiederholungen abgeschlossen!")

    self.after(300, self.poll_arduino)  # fallback: 500
