import subprocess
import re
from PyQt6.QtCore import QThread, pyqtSignal
from app.core.helpers import parse_ffmpeg_progress
from app.services.util_service import UtilService

class UtilWorker(QThread):
    progress = pyqtSignal(int)          # % Tiến độ (0-100)
    log_signal = pyqtSignal(str)        # Log xuất ra giao diện
    finished_signal = pyqtSignal(bool, str) # (Success status, Output path hoặc Lỗi)

    def __init__(
        self, 
        input_path: str, 
        output_path: str, 
        mode: str = "rotate",              # "rotate" hoặc "resize"
        rotate_option: str = None,         # Option chọn từ Rotate Block
        target_size: tuple = (0, 0),       # (width, height) dùng cho Resize Block
        duration_sec: float = 0
    ):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.mode = mode
        self.rotate_option = rotate_option
        self.target_size = target_size
        self.duration_sec = duration_sec
        self.service = UtilService()
        self._is_cancelled = False

    def run(self):
        mode_str = self.service.get_execution_mode_str()
        self.log_signal.emit(f"Starting resize & rotate process using: {mode_str}")

        # Kiểm tra MODE để gọi build_command tương ứng
        if self.mode == "rotate":
            cmd = self.service.build_rotate_command(
                self.input_path, self.output_path, self.rotate_option
            )
        elif self.mode == "resize":
            width, height = self.target_size
            cmd = self.service.build_resize_command(
                self.input_path, self.output_path, width, height
            )
        else:
            self.finished_signal.emit(False, f"Invalid mode: {self.mode}")
            return

        if not cmd:
            self.finished_signal.emit(False, "Failed to build FFmpeg command.")
            return

        self.log_signal.emit(f"Executing Command: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            for line in process.stdout:
                if self._is_cancelled:
                    process.kill()
                    self.finished_signal.emit(False, "Process cancelled by user.")
                    return
                if (pct := parse_ffmpeg_progress(line, self.duration_sec)) is not None:
                    self.progress.emit(pct)

            process.wait()

            if process.returncode == 0:
                self.progress.emit(100)
                self.finished_signal.emit(True, self.output_path)
            else:
                self.finished_signal.emit(False, f"FFmpeg failed with exit code {process.returncode}")

        except Exception as e:
            self.finished_signal.emit(False, str(e))

    def cancel(self):
        self._is_cancelled = True