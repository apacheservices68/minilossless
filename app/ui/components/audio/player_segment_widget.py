
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox

# Assuming a VideoPlayerWidget exists in the specified path
from app.ui.components.video_player_widget import VideoPlayerWidget

class PlayerSegmentWidget(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setLayout(QVBoxLayout())

        # Video Player
        self.video_player = VideoPlayerWidget(main_window=self.main_window)
        self.layout().addWidget(self.video_player)

    def set_video(self, video_path):
        self.video_player.load_video(video_path)
