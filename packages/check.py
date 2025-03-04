#!/usr/bin/env python3

import subprocess


def check_and_install_uno_core():
    # 1) Index aktualisieren (optional, wenn du das sicherstellen willst)
    subprocess.run(["arduino-cli", "core", "update-index"], check=True)

    # 2) Liste der installierten Cores abrufen
    result = subprocess.run(
        ["arduino-cli", "core", "list"], capture_output=True, text=True, check=True
    )
    installed_cores_output = result.stdout

    # 3) Prüfen, ob "arduino:avr" bereits in der Liste steht
    if "arduino:avr" in installed_cores_output:
        print("arduino:avr-Core ist bereits installiert.")
    else:
        print("arduino:avr-Core fehlt. Installation wird ausgeführt...")
        subprocess.run(["arduino-cli", "core", "install", "arduino:avr"], check=True)
        print("arduino:avr-Core wurde erfolgreich installiert.")
