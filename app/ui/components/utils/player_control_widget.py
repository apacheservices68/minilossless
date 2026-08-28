from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt6.QtCore import Qt

class PlayerControlWidget(QWidget):
    """
    A widget providing standard media player controls.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface for the player controls.
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        
        self.btn_play_pause = QPushButton("Play")
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.lbl_time = QLabel("00:00:00.000 / 00:00:00.000")
        
        self.btn_mute = QPushButton("Mute")
        self.btn_mute.setCheckable(True)
        
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(100)
        self.slider_volume.setMaximumWidth(100)
        
        layout.addWidget(self.btn_play_pause)
        layout.addWidget(self.slider_timeline)
        layout.addWidget(self.lbl_time)
        layout.addWidget(self.btn_mute)
        layout.addWidget(self.slider_volume)

        self.setLayout(layout)

    def reset_ui(self):
        """
        Resets all controls to their initial state.
        """
        self.btn_play_pause.setText("Play")
        
        self.slider_timeline.blockSignals(True)
        self.slider_timeline.setRange(0, 0)
        self.slider_timeline.setValue(0)
        self.slider_timeline.blockSignals(False)
        
        self.lbl_time.setText("00:00:00.000 / 00:00:00.000")
        
        self.btn_mute.setChecked(False)
        
        self.slider_volume.blockSignals(True)
        self.slider_volume.setValue(100)
        self.slider_volume.blockSignals(False)
