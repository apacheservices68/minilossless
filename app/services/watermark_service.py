from PyQt6.QtCore import QThread, pyqtSignal
import app.services.ffmpeg_service as ffmpeg_service
import app.services.img_watermark_service as img_watermark_service
### Author : @apacheservices68 
### Add on 08142026: Dinh nghia luong nguyen thuy cho watermark hinh anh va watermark van ban / Define a universal thread for image and text watermarking
class UniversalWatermarkWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(
        self, 
        watermark_type: str,  # "text" hoặc "image"
        video_path: str, 
        output_path: str, 
        position: str, 
        text: str = "", 
        image_path: str = "", 
        parent=None
    ):
        super().__init__(parent)
        self.watermark_type = watermark_type
        self.video_path = video_path
        self.output_path = output_path
        self.position = position
        self.text = text
        self.image_path = image_path

    def run(self):
        try:
            self.log_signal.emit(f"Starting {self.watermark_type} watermark process...")

            if self.watermark_type == "image":
                img_watermark_service.apply_image_watermark(
                    self.video_path, self.output_path, self.image_path, self.position
                )
            else:  # "text"
                ffmpeg_service.watermark_video(
                    self.video_path, self.output_path, self.text, self.position
                )

            final_message = f"Successfully saved watermarked video to: {self.output_path}"
            self.log_signal.emit(final_message)
            self.finished_signal.emit(final_message)

        except Exception as e:
            error_message = f"Failed to apply {self.watermark_type} watermark: {str(e)}"
            self.log_signal.emit(error_message)
            self.error_signal.emit(error_message)