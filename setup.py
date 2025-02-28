#!/usr/bin/env python3

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
            "paparazzo=paparazzo.gui:main",  # main() in gui.py als Einstiegspunkt
        ],
    },
)
