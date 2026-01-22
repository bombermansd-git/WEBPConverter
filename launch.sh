#!/bin/bash

# Name of the virtual environment folder
VENV_DIR="venv"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Activate venv
source $VENV_DIR/bin/activate

# Upgrade pip and install requirements
echo "Checking for updates to requirements..."
python3 -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Run the converter script
echo "Launching Converter..."
python converter.py

# Deactivate when closed
deactivate
