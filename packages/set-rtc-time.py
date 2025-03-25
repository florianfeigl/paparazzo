#!/usr/bin/env python3

import board
import busio
import adafruit_ds3231
import time
from datetime import datetime

# I2C-Verbindung & RTC initialisieren
i2c = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_ds3231.DS3231(i2c)

# Aktuelle Systemzeit holen
now = datetime.now()

# Umwandeln in struct_time für DS3231
now_struct = time.struct_time((
    now.year, now.month, now.day,
    now.hour, now.minute, now.second,
    now.weekday(), -1, -1
))

# In RTC schreiben
rtc.datetime = now_struct

print("✅ RTC-Zeit gesetzt auf:", rtc.datetime)
