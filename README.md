# Meade Autoguider Complete 4.2.0

Denne samlede version indeholder:

- framebuffer-display på `/dev/fb1`
- ADS7846 touch på `/dev/input/event4`
- SSH- og lokalt USB-tastatur
- AutoStar #497 via USB-RS232
- Mount-status
- Mount Test med N/S/E/W, STOP og pulslængde
- USB-kamera på `/dev/video0`
- live preview
- stjernedetektion
- valg/frigivelse af guide-stjerne
- logning

Denne version indeholder endnu ikke automatisk kalibrering eller automatisk guiding.

## Installation

Kopiér hele mappen til:

```text
/home/rpi/meade_autoguider
```

Installer afhængigheder:

```bash
sudo apt update
sudo apt install python3-opencv python3-numpy python3-evdev python3-serial
sudo usermod -aG input,dialout rpi
```

Genstart hvis gruppemedlemskab lige er ændret.

## Syntakstest

```bash
cd ~/meade_autoguider
source ~/opencv-env/bin/activate
python3 -m py_compile main.py gui/*.py mount/*.py camera/*.py system/*.py
```

## Start

```bash
python3 main.py
```

## Tastatur

Menu:
- `n`: næste
- `p`: forrige
- `v` eller Enter: vælg
- `q` eller Esc: tilbage

Mount Test:
- `n`, `s`, `e`, `w`
- `x`: STOP
- `+`, `-`
- `q`: tilbage

Camera:
- `n`: næste stjerne
- `v`: vælg/lås
- `r`: frigiv
- `q`: tilbage
# meade_autoguider
