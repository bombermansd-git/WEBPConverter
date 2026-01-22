import sys
import os
import shutil
import platform
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QCheckBox, QFileDialog, QMessageBox, QFrame, 
                             QGridLayout, QStackedLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QPoint, QEvent, QSize
from PyQt6.QtGui import QDesktopServices, QPainter, QColor, QBrush, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Custom Range Slider Widget ---
class RangeSlider(QWidget):
    """
    A custom slider with two handles (Start and End) to select a time range.
    """
    rangeChanged = pyqtSignal(int, int) # Emits (start_val, end_val)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.min_val = 0
        self.max_val = 100
        self.start_pos = 0
        self.end_pos = 100
        
        # UI State
        self.dragging_start = False
        self.dragging_end = False
        self.handle_width = 14
        
        # Colors
        self.track_color = QColor("#444444")
        self.selection_color = QColor("#0d6efd")
        self.handle_color = QColor("#ffffff")

    def set_range(self, minimum, maximum):
        self.min_val = minimum
        self.max_val = maximum
        self.start_pos = minimum
        self.end_pos = maximum
        self.update()

    def get_range(self):
        return self.start_pos, self.end_pos

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Geometry
        width = self.width()
        height = self.height()
        track_y = height // 2 - 2
        
        # Draw Background Track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.track_color))
        painter.drawRoundedRect(0, track_y, width, 4, 2, 2)

        # Draw Selected Range
        start_x = self._val_to_x(self.start_pos)
        end_x = self._val_to_x(self.end_pos)
        
        painter.setBrush(QBrush(self.selection_color))
        painter.drawRoundedRect(start_x, track_y, end_x - start_x, 4, 2, 2)

        # Draw Handles
        self._draw_handle(painter, start_x, track_y + 2)
        self._draw_handle(painter, end_x, track_y + 2)

    def _draw_handle(self, painter, x, cy):
        painter.setBrush(QBrush(self.handle_color))
        painter.drawEllipse(QPoint(int(x), int(cy)), 7, 7)

    def _val_to_x(self, val):
        if self.max_val == self.min_val: return 0
        ratio = (val - self.min_val) / (self.max_val - self.min_val)
        return int(ratio * (self.width() - self.handle_width)) + self.handle_width // 2

    def _x_to_val(self, x):
        effective_width = self.width() - self.handle_width
        ratio = (x - self.handle_width // 2) / effective_width
        ratio = max(0, min(1, ratio))
        return int(ratio * (self.max_val - self.min_val) + self.min_val)

    def mousePressEvent(self, event):
        x = event.pos().x()
        start_x = self._val_to_x(self.start_pos)
        end_x = self._val_to_x(self.end_pos)
        
        # Check which handle is closer or clicked
        dist_start = abs(x - start_x)
        dist_end = abs(x - end_x)
        
        if dist_start < 15 and dist_start <= dist_end:
            self.dragging_start = True
        elif dist_end < 15:
            self.dragging_end = True
        
        # If clicked on the bar, jump the closest handle
        if not self.dragging_start and not self.dragging_end:
            if dist_start < dist_end:
                self.start_pos = self._x_to_val(x)
                self.dragging_start = True
            else:
                self.end_pos = self._x_to_val(x)
                self.dragging_end = True
            self.update()
            self.rangeChanged.emit(self.start_pos, self.end_pos)

    def mouseMoveEvent(self, event):
        val = self._x_to_val(event.pos().x())
        
        if self.dragging_start:
            self.start_pos = min(val, self.end_pos) # Start cannot go past End
        elif self.dragging_end:
            self.end_pos = max(val, self.start_pos) # End cannot go past Start
            
        if self.dragging_start or self.dragging_end:
            self.update()
            self.rangeChanged.emit(self.start_pos, self.end_pos)

    def mouseReleaseEvent(self, event):
        self.dragging_start = False
        self.dragging_end = False

# --- Worker Thread ---
class ConversionWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(self.cmd, check=True, startupinfo=startupinfo)
            self.finished.emit()
        except subprocess.CalledProcessError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))

# --- Main App ---
class WebPConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to WEBP Converter")
        self.resize(550, 850) 
        
        self.ffmpeg_path = None
        self.home_dir = str(Path.home())
        self.current_dir = self.home_dir
        self.last_output_file = None
        
        # Player State
        self.duration_ms = 0
        self.is_playing = False
        self.is_muted = True # Default to muted

        # Setup Main Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        self._apply_dark_theme()
        self._build_ui()
        self._setup_player()
        
        QThread.msleep(100)
        self._check_ffmpeg()

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
            QLabel { font-size: 13px; color: #cccccc; }
            QLabel#Header { font-size: 15px; font-weight: bold; color: #ffffff; }
            QLabel#TimeLabel { font-size: 12px; font-weight: bold; color: #aaaaaa; }
            QLabel#Placeholder { font-size: 14px; color: #555555; background-color: black; border-radius: 4px; }
            QLineEdit { padding: 8px; border: 1px solid #3e3e3e; border-radius: 4px; background-color: #2d2d2d; color: #ffffff; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #4a90e2; background-color: #333333; }
            QPushButton { padding: 0px; border-radius: 4px; font-size: 13px; border: 1px solid #3e3e3e; background-color: #333333; color: #ffffff; }
            QPushButton:hover { background-color: #444444; }
            QPushButton#ConvertBtn { background-color: #0d6efd; color: white; font-weight: bold; font-size: 14px; padding: 12px; border: none; }
            QPushButton#ConvertBtn:hover { background-color: #0b5ed7; }
            QPushButton#ConvertBtn:disabled { background-color: #2a2a2a; color: #666666; }
            QFrame#SettingsBox, QFrame#VideoBox { background-color: #252526; border: 1px solid #333333; border-radius: 8px; }
            QCheckBox { font-size: 13px; spacing: 8px; color: #e0e0e0; }
            QMessageBox { background-color: #252526; }
            QMessageBox QLabel { color: #e0e0e0; }
        """)

    def _build_ui(self):
        # --- Input Section ---
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        lbl_input = QLabel("Source Video File")
        lbl_input.setObjectName("Header")
        input_layout.addWidget(lbl_input)
        path_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select a video file...")
        self.path_input.setReadOnly(True)
        path_row.addWidget(self.path_input)
	
        # Browse Button (Standard size)
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setFixedSize(80, 32)
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.clicked.connect(self._browse_file)
        path_row.addWidget(self.btn_browse)
        input_layout.addLayout(path_row)
        self.main_layout.addWidget(input_container)

        # --- Video Player Section ---
        self.video_container = QFrame()
        self.video_container.setObjectName("VideoBox")
        self.video_container.setFixedHeight(400) 
        vbox_video = QVBoxLayout(self.video_container)
        vbox_video.setContentsMargins(10, 10, 10, 10)

        # 1. Stacked Layout for Video/Placeholder
        self.video_stack_widget = QWidget()
        self.video_stack = QStackedLayout(self.video_stack_widget)
        self.video_stack.setStackingMode(QStackedLayout.StackingMode.StackOne)
        
        # Layer 0: Placeholder
        self.lbl_placeholder = QLabel("No Video Loaded")
        self.lbl_placeholder.setObjectName("Placeholder")
        self.lbl_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_stack.addWidget(self.lbl_placeholder)
        
        # Layer 1: Video Widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_stack.addWidget(self.video_widget)
        
        vbox_video.addWidget(self.video_stack_widget, stretch=1)
        
        # 2. Controls
        self.range_slider = RangeSlider()
        self.range_slider.setEnabled(False)
        self.range_slider.rangeChanged.connect(self._on_range_changed)
        vbox_video.addWidget(self.range_slider)
        
        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setObjectName("TimeLabel")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setFixedHeight(20) 
        vbox_video.addWidget(self.lbl_time)

        # --- Button Row (Play + Mute) ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10) # Gap between Play and Mute
        btn_layout.addStretch() # Push to center
        
        # Play Button
        self.btn_play = QPushButton("Play Preview")
        self.btn_play.setFixedSize(120, 36) # Fixed Height 36
        self.btn_play.clicked.connect(self._toggle_playback)
        self.btn_play.setEnabled(False)
        btn_layout.addWidget(self.btn_play)
        
        # Mute Button (Square, same height as Play)
        self.btn_mute = QPushButton()
        self.btn_mute.setFixedSize(36, 36) # 36x36 Square
        # Use resource_path for PyInstaller compatibility
        self.btn_mute.setIcon(QIcon(resource_path("muted.png"))) 
        self.btn_mute.setIconSize(QSize(20, 20))
        self.btn_mute.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mute.clicked.connect(self._toggle_mute)
        self.btn_mute.setEnabled(False) # Disabled until video loads
        btn_layout.addWidget(self.btn_mute)
        
        btn_layout.addStretch() # Push to center
        vbox_video.addLayout(btn_layout)

        self.main_layout.addWidget(self.video_container)

        # --- Settings Section ---
        settings_frame = QFrame()
        settings_frame.setObjectName("SettingsBox")
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(20, 20, 20, 20)

        lbl_settings = QLabel("Configuration")
        lbl_settings.setObjectName("Header")
        settings_layout.addWidget(lbl_settings)

        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.chk_loop = QCheckBox("Loop Animation Indefinitely")
        self.chk_loop.setChecked(True)
        grid.addWidget(self.chk_loop, 0, 0, 1, 2) 

        lbl_scale = QLabel("Scale Height (px):")
        self.txt_scale = QLineEdit("480")
        self.txt_scale.editingFinished.connect(lambda: self._validate_entry(self.txt_scale, "480"))
        grid.addWidget(lbl_scale, 1, 0)
        grid.addWidget(self.txt_scale, 1, 1)

        lbl_fps = QLabel("Frame Rate (FPS):")
        self.txt_fps = QLineEdit("24")
        self.txt_fps.editingFinished.connect(lambda: self._validate_entry(self.txt_fps, "24"))
        grid.addWidget(lbl_fps, 2, 0)
        grid.addWidget(self.txt_fps, 2, 1)
        grid.setColumnStretch(2, 1) 

        settings_layout.addLayout(grid)
        self.main_layout.addWidget(settings_frame)

        self.main_layout.addStretch()

        # --- Convert Button ---
        self.btn_convert = QPushButton("Convert to WEBP")
        self.btn_convert.setObjectName("ConvertBtn")
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.clicked.connect(self._start_conversion)
        self.main_layout.addWidget(self.btn_convert)

    def _toggle_mute(self):
        self.is_muted = not self.is_muted
        self.audio_output.setMuted(self.is_muted)
        
        if self.is_muted:
            self.btn_mute.setIcon(QIcon(resource_path("muted.png")))
        else:
            self.btn_mute.setIcon(QIcon(resource_path("mute_button.png")))

    def _setup_player(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput() 
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        self.audio_output.setMuted(True) 
        
        self.media_player.durationChanged.connect(self._media_duration_changed)
        self.media_player.positionChanged.connect(self._media_position_changed)
        self.media_player.errorOccurred.connect(self._media_error)

    def _media_error(self):
        err_msg = self.media_player.errorString()
        print(f"Media Player Error: {err_msg}")

    def _browse_file(self):
        file_filter = "Video Files (*.mp4 *.mov *.avi *.mkv *.flv *.wmv);;All Files (*)"
        fname, _ = QFileDialog.getOpenFileName(self, "Select Video", self.current_dir, file_filter)
        if fname:
            self.path_input.setText(fname)
            self.current_dir = os.path.dirname(fname)
            self._load_video(fname)

    def _load_video(self, file_path):
        self.video_stack.setCurrentWidget(self.video_widget)
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.btn_play.setEnabled(True)
        self.btn_mute.setEnabled(True)
        self.range_slider.setEnabled(True)
        self.btn_play.setText("Play Preview")
        
    def _toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.btn_play.setText("Play Preview")
        else:
            start_ms, end_ms = self.range_slider.get_range()
            if self.media_player.position() >= end_ms or self.media_player.position() < start_ms:
                self.media_player.setPosition(start_ms)
            
            self.media_player.play()
            self.btn_play.setText("Pause") 

    def _media_duration_changed(self, duration):
        self.duration_ms = duration
        self.range_slider.set_range(0, duration)
        self._update_time_label()

    def _media_position_changed(self, position):
        start_ms, end_ms = self.range_slider.get_range()
        
        if position >= end_ms and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.setPosition(start_ms)
        
        self._update_time_label()

    def _on_range_changed(self, start, end):
        if self.sender().dragging_start:
             self.media_player.setPosition(start)
        elif self.sender().dragging_end:
             self.media_player.setPosition(end)
        self._update_time_label()

    def _update_time_label(self):
        start, end = self.range_slider.get_range()
        s_sec = start // 1000
        e_sec = end // 1000
        self.lbl_time.setText(f"Trim: {s_sec}s - {e_sec}s")

    def _validate_entry(self, widget, default_val):
        if not widget.text().strip():
            widget.setText(default_val)

    def _check_ffmpeg(self):
        if shutil.which("ffmpeg") or shutil.which("ffmpeg", path=os.getcwd()):
            self.ffmpeg_path = shutil.which("ffmpeg") or shutil.which("ffmpeg", path=os.getcwd())
        else:
            QMessageBox.warning(self, "FFMPEG Missing", "FFMPEG not found. Install it to convert.")
            self.btn_convert.setEnabled(False)

    def _start_conversion(self):
        if not self.ffmpeg_path: return

        input_file = self.path_input.text()
        if not input_file: return

        p = Path(input_file)
        output_file = p.with_suffix('.webp')
        self.last_output_file = str(output_file)

        scale = self.txt_scale.text()
        fps = self.txt_fps.text()
        loop = self.chk_loop.isChecked()
        loop_val = "0" if loop else "1"

        start_ms, end_ms = self.range_slider.get_range()
        start_sec = start_ms / 1000.0
        duration_sec = (end_ms - start_ms) / 1000.0

        cmd = [
            self.ffmpeg_path,
            "-ss", str(start_sec),
            "-t", str(duration_sec),
            "-i", input_file,
            "-c:v", "libwebp",
            "-loop", loop_val,
            "-vf", f"scale=-1:{scale},fps={fps}",
            str(output_file),
            "-y"
        ]

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("Converting...")
        
        self.worker = ConversionWorker(cmd)
        self.worker.finished.connect(self._conversion_success)
        self.worker.error.connect(self._conversion_error)
        self.worker.start()

    def _conversion_success(self):
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("Convert to WEBP")
        msg = QMessageBox(self)
        msg.setWindowTitle("Success")
        msg.setText("Conversion Complete!")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("QLabel{min-width: 300px; color: #e0e0e0;} QMessageBox{background-color: #252526;}")
        btn_open = msg.addButton("Open Output Folder", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msg.exec()
        if msg.clickedButton() == btn_open:
            folder_path = os.path.dirname(self.last_output_file)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

    def _conversion_error(self, err_msg):
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("Convert to WEBP")
        QMessageBox.critical(self, "Error", f"FFMPEG Error:\n{err_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    window = WebPConverterApp()
    window.show()
    sys.exit(app.exec())
