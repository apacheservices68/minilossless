# app/ui/components/track_control_widget.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

class TrackControlWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.tracks = []
        self.is_audio_discarded = False
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        self.btn_tracks_status = QPushButton("Tracks (0/0)")
        self.btn_toggle_audio = QPushButton("Keep audio")
        self.btn_toggle_audio.setCheckable(True)
        self.btn_toggle_audio.setChecked(False)

        layout.addWidget(self.btn_tracks_status)
        layout.addWidget(self.btn_toggle_audio)
        layout.addStretch()
