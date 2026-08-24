import subprocess
import re
from PyQt6.QtCore import QThread, pyqtSignal
from app.services.crop_service import CropService

class CropWorker(QThread):
    progress = pyqtSignal(int)          # % Tiến độ (0-100)
    log_signal = pyqtSignal(str)        # Log xuất ra giao diện
    finished_signal = pyqtSignal(bool, str) # (Success status, Output path hoặc Lỗi)

    def __init__(self, input_path: str, output_path: str, x: int, y: int, w: int, h: int, duration_sec: float = 0):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.duration_sec = duration_sec
        self.service = CropService()
        self._is_cancelled = False

    def run(self):
        mode_str = self.service.get_execution_mode_str()
        self.log_signal.emit(f"Starting Crop process using: {mode_str}")

        cmd = self.service.build_crop_command(
            self.input_path, self.output_path, self.x, self.y, self.w, self.h
        )
        # self.log_signal.emit(f"Executing Command: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

            for line in process.stdout:
                if self._is_cancelled:
                    process.kill()
                    self.finished_signal.emit(False, "Process cancelled by user.")
                    return

                # Parse tiến độ thời gian FFmpeg để tính %
                match = time_pattern.search(line)
                if match and self.duration_sec > 0:
                    hours, minutes, seconds = map(float, match.groups())
                    elapsed = hours * 3600 + minutes * 60 + seconds
                    pct = int((elapsed / self.duration_sec) * 100)
                    self.progress.emit(min(100, max(0, pct)))

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