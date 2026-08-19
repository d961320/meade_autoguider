#!/bin/bash

echo "========================================"
echo " Meade Autoguider - Syntax Check"
echo "========================================"

python3 -m py_compile \
    main.py \
    config.py \
    version.py \
    gui/*.py \
    mount/*.py \
    camera/*.py \
    system/*.py

if [ $? -eq 0 ]; then
    echo
    echo "✅ Ingen syntaksfejl fundet."
else
    echo
    echo "❌ Der blev fundet fejl."
fi
