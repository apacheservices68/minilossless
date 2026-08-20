
import traceback
import subprocess
import os
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal

from app.services.audio_service import AudioService
from app.core import audio_constants as const

class AudioWorker(QThread):
    """Worker thread for handling long-running audio processing tasks."""

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

    def stop(self):
        self._is_running = False

    def run(self):
        """The entry point for the thread. All processing happens here."""
        audio_file = None
        filter_script_path = None
        audio_filter = None
        try:
            self.log.emit("[INFO] Bắt đầu xử lý âm thanh...")
            self.progress.emit(5)

            mute_all = self.settings.get("mute_all", False)
            smart_mute = self.settings.get("smart_mute")
            segments = self.settings.get("segments", [])
            is_beep = self.settings.get("replace_beep", False)

            if segments:
                # Manual segment muting
                self.log.emit(f"[INFO] Found {len(segments)} manual segments to mute.")
                audio_filter = self.audio_service.generate_mute_filter_from_segments(segments, is_beep)
                self.progress.emit(50)
            
            elif not mute_all:
                # AI Smart Mute processing
                self.log.emit("[INFO] Đang phân tích luồng âm thanh trong video bằng AI...")
                audio_file = self.audio_service.extract_audio(self.video_file)
                if not audio_file or not self._is_running:
                    raise Exception("Trích xuất âm thanh thất bại hoặc đã bị hủy.")
                self.progress.emit(25)

                intervals = []
                if smart_mute and audio_file and self._is_running:
                    intervals = self.audio_service.find_speech_intervals(
                        audio_file,
                        self.settings.get("threshold", const.THRESHOLD_DEFAULT),
                        self.settings.get("min_duration", const.DURATION_DEFAULT),
                        self.settings.get("padding", const.PADDING_DEFAULT)
                    )
                    self.log.emit(f"[INFO] Đã phát hiện {len(intervals)} đoạn giọng nói. Đang tiến hành xử lý và render video đầu ra...")
                self.progress.emit(50)

                if not self._is_running: return
                total_duration = self.get_video_duration()
                
                ffmpeg_script_content = ""
                if smart_mute and intervals:
                    ffmpeg_script_content = self.audio_service.generate_ffmpeg_filter_script(
                        intervals, total_duration
                    )
                
                if ffmpeg_script_content:
                    with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as tmp_file:
                        filter_script_path = tmp_file.name
                        tmp_file.write(f"[0:a]{ffmpeg_script_content}[a]")

            
            self.progress.emit(60)

            # Step 4: Run FFmpeg to export the final video
            if not self._is_running: return
            self.log.emit("[INFO] Đang áp dụng bộ lọc và render video...")
            self.run_ffmpeg_export(filter_script_path, mute_all, audio_filter)
            self.progress.emit(100)
            
            if self._is_running:
                self.log.emit(f"[INFO] Đã xuất video thành công: {self.output_path}")
                self.finished.emit(True, self.output_path)

        except Exception as e:
            err_msg = traceback.format_exc()
            self.log.emit(f"[LỖI] Đã xảy ra lỗi:\n{err_msg}")
            self.finished.emit(False, str(e))

        finally:
            # Step 5: Clean up temporary files
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
                "ffmpeg", "-y", "-i", self.video_file,
                "-c:v", "copy",
                "-an",  # No audio
                self.output_path
            ]
        elif audio_filter:
             command = [
                "ffmpeg", "-y", "-i", self.video_file,
                "-c:v", "copy",
                "-af", audio_filter,
                self.output_path
            ]
        elif filter_script_path:
            command = [
                "ffmpeg", "-y", "-i", self.video_file,
                "-filter_complex_script", filter_script_path,
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                self.output_path
            ]
        else:  # No audio processing needed, just copy the original video
            self.log.emit("[INFO] No audio processing needed. Copying video stream directly.")
            command = ["ffmpeg", "-y", "-i", self.video_file, "-c:v", "copy", "-c:a", "copy", self.output_path]

        cmd_str = " ".join(command)

        # self.log.emit(f"[DEBUG] Running FFmpeg command: {cmd_str}")

        try:
            # Using subprocess.run to wait for completion and capture output
            # This is better for preventing hung processes.
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
            # for line in result.stderr.splitlines(): # FFmpeg logs progress to stderr
                # self.log.emit(line.strip())

        except subprocess.CalledProcessError as e:
            self.log.emit("--- FFmpeg Error Output ---")
            # The full stderr is captured, which is useful for debugging
            self.log.emit(e.stderr)
            self.log.emit("---------------------------")
            raise Exception("FFmpeg export failed. See log for details.")

    def __del__(self):
        self.wait()
