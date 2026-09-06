from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QLineEdit, 
    QSlider, QPushButton, QHBoxLayout, QCheckBox, QTextEdit
)
from PyQt6.QtCore import Qt

class NewFeaturesTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Snapshot & Frame Extraction ---
        snapshot_group = QGroupBox("Snapshot & Frame Extraction")
        snapshot_layout = QFormLayout()

        self.snapshot_format = QComboBox()
        self.snapshot_format.addItems(["JPG", "PNG"])
        snapshot_layout.addRow("Format:", self.snapshot_format)

        self.snapshot_filename = QLineEdit("[filename]_Frame_[timestamp]")
        snapshot_layout.addRow("Filename Pattern:", self.snapshot_filename)

        self.snapshot_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.snapshot_quality_slider.setRange(1, 100)
        self.snapshot_quality_slider.setValue(90)
        snapshot_layout.addRow("Quality:", self.snapshot_quality_slider)

        btn_take_snapshot = QPushButton("Take Snapshot at Current Time")
        btn_take_snapshot.clicked.connect(self.take_snapshot_action)
        snapshot_layout.addRow(btn_take_snapshot)

        snapshot_group.setLayout(snapshot_layout)
        main_layout.addWidget(snapshot_group)

        # --- Change FPS ---
        fps_group = QGroupBox("Change FPS (for No-Cut Exports)")
        fps_layout = QFormLayout()
        self.fps_input = QLineEdit()
        self.fps_input.setPlaceholderText("e.g., 24, 25, 30, 60")
        fps_layout.addRow("New FPS:", self.fps_input)
        fps_group.setLayout(fps_layout)
        main_layout.addWidget(fps_group)

        # --- Track & Metadata Management ---
        track_group = QGroupBox("Track & Metadata Management")
        track_layout = QVBoxLayout()
        
        # Audio Tracks
        audio_track_layout = QHBoxLayout()
        self.keep_all_audio = QCheckBox("Keep all audio tracks")
        self.keep_all_audio.setChecked(True)
        self.remove_all_audio = QCheckBox("Remove all audio tracks")
        audio_track_layout.addWidget(self.keep_all_audio)
        audio_track_layout.addWidget(self.remove_all_audio)
        track_layout.addLayout(audio_track_layout)

        # Video Tracks
        video_track_layout = QHBoxLayout()
        self.keep_all_video = QCheckBox("Keep all video tracks")
        self.keep_all_video.setChecked(True)
        self.remove_all_video = QCheckBox("Remove all video tracks")
        video_track_layout.addWidget(self.keep_all_video)
        video_track_layout.addWidget(self.remove_all_video)
        track_layout.addLayout(video_track_layout)

        # Metadata
        metadata_group = QGroupBox("Metadata (leave empty to keep original)")
        metadata_layout = QFormLayout()
        self.metadata_input = QTextEdit()
        self.metadata_input.setPlaceholderText("key1=value1\nkey2=value2")
        metadata_layout.addRow(self.metadata_input)
        metadata_group.setLayout(metadata_layout)
        track_layout.addWidget(metadata_group)
        
        track_group.setLayout(track_layout)
        main_layout.addWidget(track_group)

        main_layout.addStretch()

    def take_snapshot_action(self):
        # Logic to be implemented
        self.main_window.log("Snapshot feature not yet implemented.")
        pass

    def get_export_options(self):
        """Gathers all export options from this tab."""
        options = {
            'fps': self.fps_input.text().strip(),
            'keep_audio': self.keep_all_audio.isChecked(),
            'remove_audio': self.remove_all_audio.isChecked(),
            'keep_video': self.keep_all_video.isChecked(),
            'remove_video': self.remove_all_video.isChecked(),
            'metadata': self.metadata_input.toPlainText().strip()
        }
        return options
