#!/usr/bin/env bash

# Dependencies 
sudo apt update && sudo apt upgrade
sudo apt install libcap-dev libatlas-base-dev ffmpeg libopenjp2-7
sudo apt install libcamera-dev
sudo apt install libkms++-dev libfmt-dev libdrm-dev
sudo apt install arduino
sudo apt install i2c-tools
arduino-cli lib install "AccelStepper"
arduino-cli lib install "RTClib"

# Variables
WORK_DIR = $USER/Paparazzo

# Work tree
mkdir -p $USER/Paparazzo/{packages, logs, images}

# Virtual environment
python -m venv env --system-site-packages # um picamera2/libcamera für venv verfügbar zu machen
source $USER/Paparazzo/env/bin/activate

# Desktop Verknüpfungen
ln -s $USER/Paparazzo/logs $USER/Desktop/LOGS
ln -s $USER/Paparazzo/images $USER/Desktop/IMAGES
