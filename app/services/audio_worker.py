import traceback
import subprocess
import os
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal

from app.core.constants import FFMPEG_COMMANDS
from app.core.ffmpeg_config import FFMPEG_CONFIGS, FFMPEG_PATH
from app.core.helpers import parse_ffmpeg_progress
from app.services.audio_service import AudioService
from app.core import audio_constants as const

class AudioWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str) # success, output_path

    def __init__(self, video_file, output_path, settings, parent=None):
        super().__init__(parent)
        self.video_file = video_file
        self.output_path = output_path
        self.settings = settings
        self.audio_service = AudioService()
        self._is_running = True
        self._is_cancelled = False  # <--- BỔ SUNG CỜ HỦY
        self.process = None          # <--- LƯU TIẾN TRÌNH SUBPROCESS

    def cancel(self):
        """Hủy worker và kill ngay tiến trình FFmpeg đang chạy."""
        self._is_cancelled = True
        self._is_running = False
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
            except Exception:
                pass

    def stop(self):
        self.cancel()

    def run(self):
        audio_file = None
        filter_script_path = None
        audio_filter = None
        try:
            if self._is_cancelled:
                self.finished.emit(False, "Process cancelled by user.")
                return
            self.log.emit("[INFO] Bắt đầu xử lý âm thanh...")
            self.progress.emit(5)

            mute_all = self.settings.get("mute_all", False)
            smart_mute = self.settings.get("smart_mute")
            segments = self.settings.get("segments", [])
            is_beep = self.settings.get("replace_beep", False)

            if segments:
                self.log.emit(f"[INFO] Found {len(segments)} manual segments to mute.")
                audio_filter = self.audio_service.generate_mute_filter_from_segments(segments, is_beep)
                self.progress.emit(50)
            
            elif not mute_all:
                self.log.emit("[INFO] Đang phân tích luồng âm thanh trong video bằng AI...")
                audio_file = self.audio_service.extract_audio(self.video_file)
                if not audio_file or not self._is_running:
                    raise Exception("Trích xuất âm thanh thất bại hoặc đã bị hủy.")
                self.progress.emit(25)

                intervals = []
                if smart_mute and audio_file:
                    intervals = self.audio_service.find_speech_intervals(
                        audio_file,
                        self.settings.get("threshold", const.THRESHOLD_DEFAULT),
                        self.settings.get("min_duration", const.DURATION_DEFAULT),
                        self.settings.get("padding", const.PADDING_DEFAULT)
                    )
                    self.log.emit(f"[INFO] Đã phát hiện {len(intervals)} đoạn giọng nói...")
                self.progress.emit(50)

                try:
                    total_duration = self.get_video_duration()
                except Exception:
                    total_duration = 0.0
                
                ffmpeg_script_content = ""
                if smart_mute and intervals:
                    ffmpeg_script_content = self.audio_service.generate_ffmpeg_filter_script(
                        intervals, total_duration
                    )
                
                if ffmpeg_script_content:
                    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as tmp_file:
                        filter_script_path = tmp_file.name
                        tmp_file.write(f"[0:a]{ffmpeg_script_content}[a]")

            if self._is_cancelled or not self._is_running: return
            self.progress.emit(60)

            self.log.emit("[INFO] Đang áp dụng bộ lọc và render video...")
            self.run_ffmpeg_export(filter_script_path, mute_all, audio_filter)
            
            self.progress.emit(100)
            self.log.emit(f"[INFO] Đã xuất video thành công: {self.output_path}")
            self.finished.emit(True, self.output_path)

        except Exception as e:
            if not self._is_cancelled:
                err_msg = traceback.format_exc()
                self.log.emit(f"[LỖI] Đã xảy ra lỗi:\n{err_msg}")
                self.finished.emit(False, str(e))

        finally:
            # Clean up temporary files
            cleaned = False
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                    cleaned = True
                except OSError as e:
                    self.log.emit(f"[CẢNH BÁO] Không thể xóa file tạm {audio_file}: {e}")
            
            if filter_script_path and os.path.exists(filter_script_path):
                try:
                    os.remove(filter_script_path)
                    cleaned = True
                except OSError as e:
                    self.log.emit(f"[CẢNH BÁO] Không thể xóa file script tạm {filter_script_path}: {e}")
            
            if cleaned:
                self.log.emit("[INFO] Đã dọn dẹp các file tạm an toàn.")

    def get_video_duration(self):
        command = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", self.video_file
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return float(result.stdout)

    def run_ffmpeg_export(self, filter_script_path, mute_all=False, audio_filter=None):
        if mute_all:
            command = [
                FFMPEG_PATH, "-y", "-i", self.video_file,
                FFMPEG_COMMANDS.VIDEO_CODEC, "copy",
                FFMPEG_CONFIGS["A_MUTE"],
                self.output_path
            ]
        elif audio_filter:
             command = [
                FFMPEG_PATH, "-y", "-i", self.video_file,
                FFMPEG_COMMANDS.VIDEO_CODEC, "copy",
                FFMPEG_COMMANDS.AUDIO_FILTER, audio_filter,
                self.output_path
            ]
        elif filter_script_path:
            command = [
                FFMPEG_PATH, "-y", "-i", self.video_file,
                FFMPEG_COMMANDS.FILTER_COMPLEX, filter_script_path,
                FFMPEG_COMMANDS.MAP, "0:v",
                FFMPEG_COMMANDS.MAP, "[a]",
                FFMPEG_COMMANDS.VIDEO_CODEC, "copy",
                self.output_path
            ]
        else:
            command = [FFMPEG_PATH, "-y", "-i", self.video_file, FFMPEG_COMMANDS.VIDEO_CODEC, "copy", FFMPEG_COMMANDS.AUDIO_CODEC, "copy", self.output_path]

        try:
            # Dùng Popen để theo dõi & hỗ trợ cancel
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace"
            )

            for line in self.process.stdout:
                if self._is_cancelled:
                    self.process.kill()
                    self.finished.emit(False, "Process cancelled by user.")
                    return

            self.process.wait()
            if self.process.returncode != 0 and not self._is_cancelled:
                raise Exception(f"FFmpeg process exited with code {self.process.returncode}")

        except Exception as e:
            if not self._is_cancelled:
                raise Exception(f"FFmpeg export failed: {e}")

    def __del__(self):
        self.wait()