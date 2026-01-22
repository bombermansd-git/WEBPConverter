@echo off
SETLOCAL

:: Name of the virtual environment folder
set VENV_DIR=venv

:: Check if version argument is provided
if "%~1"=="" (
    echo Error: Please provide a version number.
    echo Usage: package_windows.bat v1.0.1
    exit /b 1
)

set VERSION=%1
set APP_NAME=WEBPConverter
set EXE_NAME=WEBPConverter.exe

:: Activate venv
call %VENV_DIR%\Scripts\activate.bat

:: Generate self-contained executable
pyinstaller --noconsole --onefile --add-data "mute_button.png;." --add-data "muted.png;." --name "%APP_NAME%" converter.py

:: 1. Create the filename
set OUTPUT_FILE=%APP_NAME%-%VERSION%-windows-x86_64.zip

echo 📦 Packaging %OUTPUT_FILE%...

:: 2. Run the tar command (using -a for zip and -C to flatten)
:: Note: This requires Windows 10 (build 17063) or later
tar -a -c -f "%OUTPUT_FILE%" -C dist "%EXE_NAME%" -C .. README.md LICENSE

echo ✅ Done! Artifact created:
echo    - %OUTPUT_FILE%

:: Deactivate when closed
deactivate
ENDLOCAL
