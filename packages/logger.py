#!/usr/bin/env python3

import logging
import os
import time

import board
import busio
import adafruit_ds3231

from packages.config import LOGS_DIR

# Globale Variable für GUI-Referenz
gui_instance = None
logger = None  # Globale Logger-Variable
rtc = None     # Globale RTC-Instanz

# RTC initialisieren
def init_rtc():
    global rtc
    if rtc is None:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            rtc = adafruit_ds3231.DS3231(i2c)
        except Exception as e:
            print(f"Fehler bei der RTC-Initialisierung: {e}")
            rtc = None

# RTC-Zeit holen
def get_rtc_time():
    global rtc
    if rtc is None:
        init_rtc()
    if rtc is None:
        # Fallback auf Systemzeit
        print("Warnung: RTC nicht verfügbar, benutze Systemzeit.")
        return time.localtime()

    try:
        current_time = rtc.datetime
        # Rekonstruiere struct_time mit korrektem tm_yday, falls -1
        if current_time.tm_yday == -1:
            corrected = time.struct_time((
                current_time.tm_year, current_time.tm_mon, current_time.tm_mday,
                current_time.tm_hour, current_time.tm_min, current_time.tm_sec,
                current_time.tm_wday,
                time.localtime().tm_yday,  # Dummy-Wert oder Berechnung
                current_time.tm_isdst
            ))
            return corrected
        return current_time
    except Exception as e:
        print(f"Fehler beim Auslesen der RTC: {e}")
        return time.localtime()

# TextWidgetHandler
class TextWidgetHandler(logging.Handler):
    def emit(self, record):
        if record.levelno < logging.INFO:
            return

        msg = self.format(record)

        if gui_instance and hasattr(gui_instance, "log_text"):
            try:
                if gui_instance.log_text.winfo_exists():
                    gui_instance.after(0, self.safe_insert, msg)
                else:
                    print("GUI log_text widget existiert nicht mehr.")
                    print(msg)
            except Exception as e:
                print(f"Fehler beim Logging-Handler (Widget existiert nicht mehr): {e}")
                print(msg)
        else:
            print(msg)

    def safe_insert(self, msg):
        if gui_instance is not None:
            try:
                gui_instance.log_text.insert("end", msg + "\n")
                gui_instance.log_text.see("end")
            except Exception as e:
                print(f"Fehler beim Einfügen ins GUI-Log: {e}")


def setup_logging():
    global logger
    if logger is not None:
        return logger

    # Zeitstempel von RTC holen
    rtc_now = get_rtc_time()
    try:
        now_str = time.strftime("run_%Y%m%d_%H%M%S", rtc_now)
    except ValueError as e:
        print(f"⚠️ Fehler beim Formatieren der RTC-Zeit: {e}")
        rtc_now = time.localtime()
        now_str = time.strftime("run_%Y%m%d_%H%M%S", rtc_now)

    logger = logging.getLogger("Paparazzo")
    logger.setLevel(logging.DEBUG)  # Erfasst alle Meldungen ab DEBUG

    # Ein einziger FileHandler für alle Loglevel
    log_filename = os.path.join(LOGS_DIR, f"log_{now_str}.log")
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.DEBUG)

    # Formatter
    fmt = "[%(asctime)s] %(levelname)s: %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)
    fh.setFormatter(formatter)

    # Handler hinzufügen
    logger.addHandler(fh)

    # GUI-Handler
    th = TextWidgetHandler()
    th.setLevel(logging.DEBUG)
    th.setFormatter(formatter)
    logger.addHandler(th)

    return logger


def set_gui_instance(gui):
    """Setzt die GUI-Instanz, um Logs im Tkinter-Text-Widget anzuzeigen."""
    global gui_instance
    gui_instance = gui


def log_message(msg, level="info"):
    global logger

    if logger is None:
        logger = setup_logging()

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
