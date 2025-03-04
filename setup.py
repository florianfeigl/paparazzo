#!/usr/bin/env python3

# ----------------------------------------------------------------------------
# Author            : Florian Feigl (florian.feigl@stud.plus.ac.at)
# Supervisor        : Prof. Dr. Obermeyer (gerhard.obermeyer@plus.ac.at)
# Modified          : 04.03.2025
#
# Abstract          :
# This program serves the purpose of moving two stepper motors to scan a two
# dimensional area with cameras.
#
# Operating System  :
#   - Raspberry Pi OS 12 (bookworm)
#
# Software          :
#   - python3-full
#   - libcap-dev
#   - libcamera-dev
#   - libcamera-apps
#
# Libraries         :
#   - <AccelStepper.h>
#
# Hardware          :
#   - Arduino Uno Rev3
#   - Nema 17 Stepper Motors
#   - TB6600 Stepper Motor Drivers
#   - Raspberry Pi 4 Model B
#
# License/Disclaimer:
# This project is done in context of an academic course and can only be
# used for learning or demonstration purposes.
# ----------------------------------------------------------------------------

import os
import time
from setuptools import find_packages, setup

# Automatisch das letzte Änderungsdatum der Hauptdatei holen
project_root = os.path.dirname(os.path.abspath(__file__))
ino_file = os.path.join(project_root, "firmware", "Paparazzo.ino")  # Falls die Datei dort liegt
last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(ino_file)))

setup(
    name="paparazzo",
    version="0.6.55",
    description="Paparazzo Project: Arduino- und Kamera-Integration",
    author="Florian Feigl",
    author_email="florian.feigl@stud.plus.ac.at",
    packages=find_packages(
        include=["packages", "packages.*"]
    ),  # Findet alle Unterpakete
    package_data={"": ["firmware/*.ino"]},
    install_requires=[
        "pyserial",
        "setuptools",
    ],
    entry_points={
        "console_scripts": [
            "paparazzo=packages.gui:main",  # main() in gui.py als Einstiegspunkt
        ],
    },
)
