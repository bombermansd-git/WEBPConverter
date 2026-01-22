# Video to WEBP Converter

A modern, cross-platform GUI application written in Python (PyQt6) that converts video files to high-quality animated WEBP format. 

The application serves as a user-friendly frontend for FFMPEG, offering features like video trimming, scaling, looping control, and a built-in video player for previews.

## Features

* **Cross-Platform:** Runs on Windows, Linux, and macOS.
* **Modern GUI:** Clean, dark-themed interface built with PyQt6.
* **Video Preview:** Integrated video player to review input files before conversion.
* **Trimming:** Visual double-ended slider to select specific start and end times for the output loop.
* **Mute Toggle:** Preview videos with or without sound.
* **Custom Settings:** Control output scale (height), frame rate (FPS), and looping behavior.
* **Auto-Dependency:** Uses imageio_ffmpeg package for automatic download and integration with ffmpeg.

## Installation & Usage

### Option 1: Standalone Executable (No Python Required)
1.  Go to the [Releases](https://github.com/bombermansd-git/WEBPConverter/releases) page.
2.  Download the version for your OS
    - **Linux:** `WEBPConverter-{version}-linux-x86_64.tar.gz`
    - **Windows:** `WEBPConverter-{version}-windows-x86_64.zip`
3.  Extract the archive.
4.  Run the executable file (`./WEBPConverter` on Linux or `WEBPConverter.exe` on Windows).
5.  If FFMPEG is missing, the app will prompt you to install it automatically.

### Option 2: Running from Source
If you are a developer or want to run the raw Python script:

1.  **Prerequisites:** Ensure you have Python 3.10+ installed.
2.  **Clone the repository:**
    ```bash
    git clone https://github.com/bombermansd-git/WEBPConverter.git
    cd WEBPConverter
    ```
3.  **Set up Virtual Environment:**
    * **Windows:** `launch.bat` (Automatically creates venv, installs dependencies, and launches application)
    * **Linux/Mac:** `./launch.sh`

## Building the Executable

To package the application into a standalone file, use **PyInstaller**.

1.  Start Virtual Environment:
    * **Windows:**
        ```cmd
        venv/Scripts/activate.bat
        ```
    * **Linux/Mac:**
        ```bash
        source venv/bin/activate
        ```

1.  Install PyInstaller:
    ```cmd / bash
    pip install pyinstaller
    ```

2.  Run the build command:
    * **Windows:**
        ```cmd
        pyinstaller --noconsole --onefile --add-data "mute_button.png;." --add-data "muted.png;." --name "WEBPConverter" converter.py
        ```
    * **Linux/Mac:**
        ```bash
        pyinstaller --noconsole --onefile --add-data "mute_button.png:." --add-data "muted.png:." --name "WEBPConverter" converter.py
        ```

3.  The executable will appear in the `dist/` folder.

## Technologies Used

* **Language:** Python 3
* **GUI Framework:** PyQt6
* **Multimedia:** PyQt6-Multimedia & PyQt6-MultimediaWidgets
* **Conversion Engine:** FFMPEG via imageio_ffmpeg

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  

## Disclaimer

_Built with the assistance of Google Gemini AI._
