# app/ui/components/video_player_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSlider, QLabel, QPushButton
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt

class VideoPlayerWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.is_slider_moving = False
        self.init_ui()

    def init_ui(self):
        player_group = QGroupBox("Video Player")
        player_layout = QVBoxLayout()

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(480)
        self.video_widget.setStyleSheet("background-color: black;")
        player_layout.addWidget(self.video_widget, 1)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        timeline_layout = QHBoxLayout()
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.slider_timeline.setRange(0, 0)
        self.lbl_time = QLabel("00:00:00.000 / 00:00:00.000")
        timeline_layout.addWidget(self.slider_timeline, 1)
        timeline_layout.addWidget(self.lbl_time)
        player_layout.addLayout(timeline_layout)

        controls_layout = QHBoxLayout()
        self.btn_play_pause = QPushButton("Play")
        self.btn_set_start = QPushButton("Set Start [")
        self.btn_set_end = QPushButton("Set End ]")
        self.btn_prev_seg = QPushButton("< Prev Segment")
        self.btn_next_seg = QPushButton("Next Segment >")
        self.btn_help_close = QPushButton("?")
        self.btn_help_close.setFixedWidth(28)

        controls_layout.addWidget(self.btn_play_pause)
        controls_layout.addWidget(self.btn_set_start)
        controls_layout.addWidget(self.btn_set_end)
        controls_layout.addWidget(self.btn_prev_seg)
        controls_layout.addWidget(self.btn_next_seg)
        controls_layout.addStretch()

        # Volume Controls
        self.btn_mute = QPushButton("🔈")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setFixedWidth(30)
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(100)
        self.slider_volume.setFixedWidth(100)

        controls_layout.addWidget(self.btn_mute)
        controls_layout.addWidget(self.slider_volume)
        controls_layout.addWidget(self.btn_help_close)

        player_layout.addLayout(controls_layout)
        player_group.setLayout(player_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(player_group)
        self.setLayout(main_layout)

    def on_slider_pressed(self):
        self.is_slider_moving = True

    def on_slider_released(self):
        self.is_slider_moving = False
        self.player.setPosition(self.slider_timeline.value())

    def on_slider_moved(self, position):
        self.player.setPosition(position)
