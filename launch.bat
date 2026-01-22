@echo off
SETLOCAL

:: Name of the virtual environment folder
set VENV_DIR=venv

:: Check if venv exists, if not create it
if not exist %VENV_DIR% (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

:: Activate venv
call %VENV_DIR%\Scripts\activate.bat

:: Upgrade pip and install/update requirements
echo Checking for updates to requirements...
python -m pip install --upgrade pip
if exist requirements.txt (
    pip install -r requirements.txt
)

:: Run the converter script
echo Launching Converter...
python converter.py

:: Deactivate when closed
deactivate
ENDLOCAL
