#!/usr/bin/env bash

# Work tree
mkdir -p $USER/paparazzo/{packages, logs, images}

# Desktop Verknüpfungen
ln -s $USER/paparazzo/logs $USER/Desktop/LOGS
ln -s $USER/paparazzo/images $USER/Desktop/IMAGES

# Variables
WORK_DIR = $USER/paparazzo

# Dependencies 
sudo apt update && sudo apt upgrade
sudo apt install libcap-dev libatlas-base-dev ffmpeg libopenjp2-7
sudo apt install libcamera-dev
sudo apt install libkms++-dev libfmt-dev libdrm-dev
arduino-cli lib install "AccelStepper"

cd $WORK_DIR
