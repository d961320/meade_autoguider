#!/bin/bash

cd "$(dirname "$0")"

echo
echo "========================================"
echo "      MEADE AUTOGUIDER"
echo "========================================"
echo

# Aktivér virtuelt miljø
source ~/opencv-env/bin/activate

# Syntakskontrol
./check.sh

if [ $? -ne 0 ]; then
    echo
    echo "Programmet blev IKKE startet."
    exit 1
fi

echo
echo "Starter Meade Autoguider..."
echo

python3 main.py
