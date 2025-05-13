#!/bin/bash
set -e

echo "[1/3] Install system prerequisites"
./install-prerequisites.sh

echo "[2/3] Create venv (disabled)"
#python3 -m venv .venv
#source .venv/bin/activate

echo "[3/3] Install Python package"
pip install -r requirements.txt
pip install .

echo "Installation completed."
#echo "  source .venv/bin/activate"
