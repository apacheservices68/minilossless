from PyQt6.QtWidgets import QWidget, QVBoxLayout
from app.ui.components.video_source_widget import VideoSourceWidget
from .video_player_widget import VideoPlayerWidget
from .player_control_widget import PlayerControlWidget

class LeftLayoutWidget(QWidget):
    """
    A widget that arranges the video source, player, and controls on the left side.
    """
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface by arranging child widgets.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        self.video_source_widget = VideoSourceWidget(self)
        self.video_source_widget.file_selected.connect(self.main_window.set_active_video)
        self.video_player_widget = VideoPlayerWidget()
        self.player_controls_widget = PlayerControlWidget()

        main_layout.addWidget(self.video_source_widget)
        main_layout.addWidget(self.video_player_widget, 1) # Add stretch factor
        main_layout.addWidget(self.player_controls_widget)

        self.setLayout(main_layout)

    def reset_ui(self):
        """
        Resets the UI of all child widgets.
        """
        self.video_source_widget.set_video_path("")
        self.video_player_widget.reset_player()
        self.player_controls_widget.reset_ui()
