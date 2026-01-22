#!/bin/bash

# Name of the virtual environment folder
VENV_DIR="venv"

# Check if a version number was provided
if [ -z "$1" ]; then
  echo "Error: Please provide a version number."
  echo "Usage: ./package_linux.sh v1.0.1"
  exit 1
fi

VERSION=$1
APP_NAME="WEBPConverter"
EXE_PATH="dist/WEBPConverter"

# Activate venv
source $VENV_DIR/bin/activate
pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "mute_button.png:." --add-data "muted.png:." --name "${APP_NAME}" converter.py

# 1. Create the filename
OUTPUT_FILE="${APP_NAME}-${VERSION}-linux-x86_64.tar.gz"

echo "📦 Packaging $OUTPUT_FILE..."

# 2. Run the tar command (using -C to flatten directories)
tar -czvf "$OUTPUT_FILE" \
    -C dist "$APP_NAME" \
    -C .. README.md LICENSE

echo "✅ Done! Artifact created:"
echo "   - $OUTPUT_FILE"

# Deactivate when closed
deactivate
