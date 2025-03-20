#!/usr/bin/env python3

import os
import time
from setuptools import find_packages, setup

# Automatisch das letzte Änderungsdatum der Hauptdatei holen
project_root = os.path.dirname(os.path.abspath(__file__))
ino_file = os.path.join(project_root, "firmware", "firmware.ino")  
last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(ino_file)))

setup(
    name="paparazzo",
    version="0.8",
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
