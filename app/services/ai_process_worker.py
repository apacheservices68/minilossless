from PyQt6.QtCore import pyqtSignal, QThread

from app.services.ai_processor import AIProcessorSignals
from app.services.ffmpeg_service import process_video_ai

class AIProcessWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, input_path, output_path, texts, use_cuda, face_blur, face_blur_pct, face_blur_type, face_blur_image_path, bg_blur, bg_blur_strength, face_blur_style="Gaussian", face_blur_strength=15):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.texts = texts
        self.use_cuda = use_cuda
        self.face_blur = face_blur
        self.face_blur_pct = face_blur_pct
        self.face_blur_type = face_blur_type
        self.face_blur_image_path = face_blur_image_path
        self.bg_blur = bg_blur
        self.bg_blur_strength = bg_blur_strength
        self.face_blur_style = face_blur_style
        self.face_blur_strength = face_blur_strength

        self._is_cancelled = False

    def run(self):
        signals = AIProcessorSignals()
        signals.progress.connect(self.progress.emit)
        signals.finished.connect(self.finished.emit)
        try:
            process_video_ai(
                input_video_path=self.input_path,
                output_video_path=self.output_path,
                texts=self.texts,
                use_cuda=self.use_cuda,
                face_blur_enabled=self.face_blur,
                face_blur_pct=self.face_blur_pct,
                face_blur_type=self.face_blur_type,
                face_blur_image_path=self.face_blur_image_path,
                face_blur_style=self.face_blur_style,
                face_blur_strength=self.face_blur_strength,
                bg_blur_enabled=self.bg_blur,
                bg_blur_strength=self.bg_blur_strength,
                signals=signals,
                worker=self
            )
        except Exception as e:
            self.finished.emit(False, str(e))

    def cancel(self):
        self._is_cancelled = True  # <--- BỔ SUNG