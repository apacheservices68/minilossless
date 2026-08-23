from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt6.QtCore import Qt

class PlayerControlsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        player_controls_layout = QHBoxLayout(self)
        player_controls_layout.setContentsMargins(0, 5, 0, 0)
        
        self.btn_play_pause = QPushButton("Play")
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.lbl_time = QLabel("00:00:00.000 / 00:00:00.000")
        
        self.btn_mute = QPushButton("Mute")
        self.btn_mute.setCheckable(True)
        
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(100)
        self.slider_volume.setMaximumWidth(100)
        
        player_controls_layout.addWidget(self.btn_play_pause)
        player_controls_layout.addWidget(self.slider_timeline)
        player_controls_layout.addWidget(self.lbl_time)
        player_controls_layout.addWidget(self.btn_mute)
        player_controls_layout.addWidget(self.slider_volume)