# Paparazzo
**Author**: Florian Feigl (florian.feigl@stud.plus.ac.at)
**Supervisor**: Prof. Dr. Obermeyer (gerhard.obermeyer@plus.ac.at)

## Abstract
  This project aimes to automate the photo-documentation of the growth over time of suspended algae specimen cells in 24-well plates, while serving as an introduction lesson to realising electro-mechanical prototypes from scratch. The underlying objective was to explore the development and implementation of tools and devices that address daily work requirements and do not exist, yet. The project included a stepper motor driven system capable, designed to moving a camera system in two dimensions to document growth of set up specimen. Alongside the exploration of several kinds of hardware components, delving into software and application development was part of the knowledge gathering experience. Using a single-board-computer as operation interface, possibilities of setting up a graphical user interface upon a complete functional operating system opened up. This enables operating the device, and independently controlling the micro-controller that instructs the drivers which again operate the motors. The camera is directly attached to and controlled by the single-board-computer. This breaks the interaction between the the single-board-computer and the micro-controller down to ["make a move"] <-> ["make a picture"].

### Operating System  
   - Raspberry Pi OS 12 (bookworm)

### Software          
- arduino-cli
    - <AccelStepper.h>
    - <RTClib.h>
    - <Wire.h>
- python3.11
    - os 
    - time 
    - Tkinter
    - datetime 
    - setuptools
    - pkg_resources
    - subprocess
    - threading
    - serial
    - picamera2

### Hardware          
   - Raspberry Pi 4 Model B
   - Raspberry Pi 4 5V/3A/15W power supply
   - Arduino Uno Rev3
   - 2x 24V/2A power supply
   - totem construction elements
   - Nema 17 Stepper Motors
   - TB6600 Stepper Motor Drivers
   - Jumper cables

## Lizenz & Nutzungshinweis
Dieses Projekt wird unter der **GNU Affero General Public License v3.0 (AGPL-3.0)** veröffentlicht.  
Das bedeutet, dass jeder den Code **frei nutzen, ändern und weitergeben** kann, solange alle Änderungen ebenfalls unter der AGPL-3.0 veröffentlicht werden.

### Lehr- & Bildungsnutzung  
Die Nutzung dieses Projekts für **Lehrzwecke, Forschung und akademische Zwecke** ist ausdrücklich **erlaubt und erwünscht**.  
Studierende, Lehrende und Forschungseinrichtungen dürfen den Code ohne Einschränkungen für **didaktische und experimentelle Zwecke** verwenden.

### Kommerzielle Nutzung  
Für kommerzielle Nutzung oder Integrationen in proprietäre Systeme ist eine **separate kommerzielle Lizenz erforderlich**.  
Unternehmen, die den Code nutzen möchten, ohne ihre Änderungen unter AGPL-3.0 offenzulegen, können eine kommerzielle Lizenz erwerben.  

📩 **Kontakt für kommerzielle Lizenzen & Wartungsverträge:** [florian.feigl@stud.plus.ac.at]  

---

© [2025] [Florian Feigl / Paparazzo] – Veröffentlicht unter der **AGPL-3.0**.  
Die vollständige Lizenz kann hier eingesehen werden: [https://www.gnu.org/licenses/agpl-3.0.html](https://www.gnu.org/licenses/agpl-3.0.html)

