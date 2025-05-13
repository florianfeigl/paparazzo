#!/bin/bash
set -e

# Paparazzo Installationsskript für Raspberry Pi OS (Bookworm)

# Prüfen, ob das Skript als Root ausgeführt wird
if [ "$EUID" -eq 0 ]; then
  echo "Bitte führe das Skript nicht als root aus!"
  exit 1
fi

# Update & Upgrade
sudo apt-get update -qq
sudo apt-get upgrade -y

# Benötigte Pakete installieren
sudo apt-get install -y --no-install-recommends \
    libcap-dev libatlas-base-dev ffmpeg libopenjp2-7 \
    libcamera-dev libkms++-dev libfmt-dev libdrm-dev \
    python3 python3-pip python3-tk python3-picamera2 \
    arduino i2c-tools

# Prüfen, ob arduino-cli installiert ist
if ! command -v arduino-cli &>/dev/null; then
    echo "arduino-cli nicht gefunden, installiere jetzt arduino-cli."
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
    sudo mv bin/arduino-cli /usr/local/bin/
    rm -rf bin
fi

# Python-Pakete installieren
pip3 install --upgrade pip
pip3 install picamera2 adafruit-circuitpython-ds3231 adafruit-blinka pyserial

# Arduino-Bibliotheken installieren
arduino-cli lib install "AccelStepper"
arduino-cli lib install "RTClib"

# Benutzerrechte prüfen und setzen
for GROUP in dialout i2c; do
    if groups $(whoami) | grep -qw "$GROUP"; then
        echo "Benutzer bereits in Gruppe $GROUP."
    else
        echo "Benutzer wird zur Gruppe $GROUP hinzugefügt."
        sudo usermod -aG $GROUP $(whoami)
    fi
done

# Projektverzeichnisse erstellen
mkdir -p ~/Paparazzo/{images,logs,firmware,templates}
cd ~/Paparazzo

# Entkommentieren, falls eine Virtual environment verwendet werden soll
#python -m venv env --system-site-packages # um picamera2/libcamera für venv verfügbar zu machen
#source ~/Paparazzo/env/bin/activate

# Desktop Verknüpfungen
ln -s ~/Paparazzo/logs ~/Desktop/LOGS
ln -s ~/Paparazzo/images ~/Desktop/IMAGES

# Prüfen der Installation

# Prüfen I2C
if ! i2cdetect -y 1 &>/dev/null; then
    echo "I2C scheint nicht aktiviert zu sein. Bitte über raspi-config aktivieren."
else
    echo "I2C-Schnittstelle aktiv."
fi

# Prüfen Seriellen Port
if [ ! -e /dev/ttyACM0 ]; then
    echo "Serieller Port /dev/ttyACM0 nicht gefunden. Arduino anschließen?"
else
    echo "Serieller Port verfügbar."
fi

# Fertigstellung
cat <<EOF

Installation abgeschlossen!
Bitte starte den Raspberry Pi neu, um alle Änderungen wirksam zu machen:

    sudo reboot

EOF
