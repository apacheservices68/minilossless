# Add on 08282026
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QTransform

class VideoPlayerWidget(QWidget):
    """
    A widget for playing video content with working rotation/flip capabilities.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer()
        
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Dùng QGraphicsScene & QGraphicsVideoItem để hỗ trợ Rotate/Flip preview
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)
        
        self.player.setVideoOutput(self.video_item)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Ẩn thanh cuộn slider dọc/ngang của GraphicsView (Add on 08282026)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        layout.addWidget(self.view)
        self.setLayout(layout)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_video_to_view()

    def fit_video_to_view(self):
        if self.video_item and not self.video_item.boundingRect().isEmpty():
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def reset_player(self):
        self.player.stop()
        self.player.setSource(QUrl())
        self.apply_rotation_and_flip("None")


    def load_video(self, file_path):
        if file_path:
            self.player.setSource(QUrl.fromLocalFile(file_path))
            # Cập nhật khung scene theo kích thước video gốc (Add on 08282026)
            self.video_item.nativeSizeChanged.connect(self._on_native_size_changed)
            self.player.play()
            self.player.pause()

    def _on_native_size_changed(self, size):
        self.video_item.setSize(size)
        self.scene.setSceneRect(self.video_item.boundingRect())
        self.fit_video_to_view()

    def apply_rotation_and_flip(self, option):
        """
        Applies rotation or flip to the video item smoothly.
        """
        self.video_item.setTransform(QTransform())
        
        rect = self.video_item.boundingRect()
        if rect.isEmpty():
            return

        center_x = rect.width() / 2
        center_y = rect.height() / 2

        transform = QTransform()
        transform.translate(center_x, center_y)

        if option == "Rotate 90°":
            transform.rotate(90)
        elif option == "Rotate 180°":
            transform.rotate(180)
        elif option == "Rotate 270°":
            transform.rotate(270)
        elif option == "Horizontal Flip":
            transform.scale(-1, 1)
        elif option == "Vertical Flip":
            transform.scale(1, -1)

        transform.translate(-center_x, -center_y)
        self.video_item.setTransform(transform)
        
        # Cập nhật lại vùng hiển thị sau khi xoay/lật (Add on 08282026)
        self.scene.setSceneRect(self.video_item.mapToScene(rect).boundingRect())
        self.fit_video_to_view()