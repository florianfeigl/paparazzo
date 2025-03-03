#!/usr/bin/env python3

# ----------------------------------------------------------------------------
# Author            : Florian Feigl (florian.feigl@stud.plus.ac.at)
# Supervisor        : Prof. Dr. Obermeyer (gerhard.obermeyer@plus.ac.at)
# Modified          : 03.03.2025
# Version           : 0.6.2
#
# Abstract          :
# This program serves the purpose of moving two stepper motors to scan a two
# dimensional area with cameras.
#
# Operating System  :
#   - Raspberry Pi OS 12 (bookworm)
#
# Software          :
#   - libcamera
#   - cmake
#   - libglib2.0-dev
#   - libgstreamer1.0-dev
#   - libgstreamer-plugins-base1.0-dev
#   - pybind11-dev
#   - python3-jinja2
#   - python3-yaml
#   - python3-ply
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

from setuptools import setup, find_packages

setup(
    name="paparazzo",
    version="0.6.0",
    description="Paparazzo Project: Arduino- und Kamera-Integration",
    author="Florian Feigl",
    author_email="florian.feigl@stud.plus.ac.at",
    packages=find_packages(include=["packages", "packages.*"]),  # Findet alle Unterpakete
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
