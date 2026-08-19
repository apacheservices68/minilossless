
from PyQt6.QtCore import QThread, pyqtSignal

from app.services.audio_service import AudioService

class AudioWorker(QThread):
    """Worker thread for handling long-running audio processing tasks."""

    # Signals to update the UI
    progress_updated = pyqtSignal(int)       # Percentage (0-100)
    log_message = pyqtSignal(str)          # Log messages
    processing_finished = pyqtSignal(bool) # True for success, False for failure

    def __init__(self, video_file, settings, parent=None):
        super().__init__(parent)
        self.video_file = video_file
        self.settings = settings # Dictionary with UI settings
        self.audio_service = AudioService()

    def run(self):
        """The entry point for the thread. All processing happens here."""
        try:
            self.log_message.emit("[INFO] Starting audio processing...")
            self.progress_updated.emit(10)

            # Step 1: Extract audio
            self.log_message.emit("[INFO] Extracting audio from video...")
            audio_file = self.audio_service.extract_audio(self.video_file)
            if not audio_file:
                raise Exception("Audio extraction failed.")
            self.progress_updated.emit(30)

            # Step 2: Find speech intervals (if smart mute is enabled)
            intervals = []
            if self.settings.get("smart_mute"): 
                self.log_message.emit("[INFO] Detecting speech intervals with AI...")
                intervals = self.audio_service.find_speech_intervals(
                    audio_file,
                    self.settings.get("threshold"),
                    self.settings.get("duration"),
                    self.settings.get("padding")
                )
                self.log_message.emit(f"[INFO] Detected {len(intervals)} speech segments.")
            self.progress_updated.emit(60)

            # Step 3: Generate FFmpeg script
            self.log_message.emit("[INFO] Generating FFmpeg filter script...")
            # ffmpeg_script = self.audio_service.generate_ffmpeg_filter_script(...)
            self.progress_updated.emit(80)

            # Step 4: Run FFmpeg to export the final video
            self.log_message.emit("[INFO] Applying filters and exporting video...")
            # ... FFmpeg export logic here ...
            self.progress_updated.emit(100)
            self.log_message.emit("[SUCCESS] Process completed successfully!")
            self.processing_finished.emit(True)

        except Exception as e:
            self.log_message.emit(f"[ERROR] An error occurred: {e}")
            self.processing_finished.emit(False)

