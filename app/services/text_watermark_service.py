from PyQt6.QtCore import QThread, pyqtSignal
import app.services.ffmpeg_service as ffmpeg_service
### Author : @apacheservices68 
class WatermarkWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, input_path: str, output_path: str, text: str, position: str, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.text = text
        self.position = position

    def run(self):
        try:
            self.log_signal.emit(f"Starting text watermark process...")
            # 081426 @apacheservice68 Gọi hàm render FFmpeg nặng ở luồng ngầm
            ffmpeg_service.watermark_video(
                self.input_path, 
                self.output_path, 
                self.text, 
                self.position
            )
            
            final_message = f"Successfully saved watermarked video to: {self.output_path}"
            self.log_signal.emit(final_message)
            self.finished_signal.emit(final_message)

        except Exception as e:
            error_message = f"Failed to watermark video: {str(e)}"
            self.log_signal.emit(error_message)
            self.error_signal.emit(error_message)