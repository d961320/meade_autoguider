#!/bin/bash

PROJECT="$HOME/meade_autoguider"
BACKUP_DIR="$HOME/meade_backups"

mkdir -p "$BACKUP_DIR"

STAMP=$(date +"%Y-%m-%d_%H-%M-%S")

DEST="$BACKUP_DIR/meade_autoguider_$STAMP"

echo "========================================"
echo "   Backup af Meade Autoguider"
echo "========================================"

cp -a "$PROJECT" "$DEST"

echo
echo "Backup gemt:"
echo "$DEST"
echo
