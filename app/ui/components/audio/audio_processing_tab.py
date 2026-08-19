
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, QUrl

from app.services.audio_worker import AudioWorker
from app.ui.components.audio.segment_manager_widget import SegmentManagerWidget
from app.ui.utils import (
    toggle_play_pause, get_formatted_time_str,
    handle_player_position_changed, handle_player_duration_changed
)

from app.ui.components.audio.player_segment_widget import PlayerSegmentWidget
from app.ui.components.audio.mute_control_widget import MuteControlWidget


class AudioProcessingTab(QWidget):
    log_message = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AudioProcessingTab")
        self.video_path = None

        # Main layout
        main_layout = QHBoxLayout(self)

        # Left side: Player and Segment Manager
        self.left_widget = PlayerSegmentWidget()

        # Right side: Controls and Export
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.mute_controls = MuteControlWidget()
        self.segment_manager = SegmentManagerWidget()
        right_layout.addWidget(self.segment_manager)
        right_layout.addWidget(self.mute_controls)
        right_layout.addStretch()

        # Splitter to make layout adjustable
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 300]) # Initial size distribution

        main_layout.addWidget(splitter)
        self.connect_signals()

    def connect_signals(self):
        video_player = self.left_widget.video_player
        video_player.player.positionChanged.connect(self.on_player_position_changed)
        video_player.player.durationChanged.connect(self.on_player_duration_changed)
        video_player.player.playbackStateChanged.connect(self.on_playback_state_changed)
        
        video_player.slider_timeline.sliderPressed.connect(video_player.on_slider_pressed)
        video_player.slider_timeline.sliderReleased.connect(video_player.on_slider_released)
        video_player.slider_timeline.sliderMoved.connect(self.on_slider_moved)
        
        video_player.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.mute_controls.export_button.clicked.connect(self.start_export)

    def start_export(self):
        if not self.video_path:
            self.log_message.emit("No video file loaded.")
            return
        
        # Suggest a default output filename
        base_name = os.path.basename(self.video_path)
        name, ext = os.path.splitext(base_name)
        default_filename = os.path.join(os.path.dirname(self.video_path), f"{name}_smart_mute.mp4")

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Muted Video", default_filename, "Video Files (*.mp4)")
        if not output_path:
            return

        settings = self.mute_controls.get_settings()
        self.log_message.emit(f"Starting export with settings: {settings}")

        self.audio_worker = AudioWorker(self.video_path, output_path, settings)
        self.audio_worker.log.connect(self.log_message)
        self.audio_worker.finished.connect(lambda: self.log_message.emit("Export finished."))
        self.audio_worker.start()

    def on_playback_state_changed(self, state):
        video_player = self.left_widget.video_player
        if state == video_player.player.PlaybackState.PlayingState:
            video_player.btn_play_pause.setText("Pause")
        else:
            video_player.btn_play_pause.setText("Play")

    def toggle_play_pause(self):
        video_player = self.left_widget.video_player
        toggle_play_pause(video_player.player, video_player.btn_play_pause)

    def on_player_position_changed(self, position):
        video_player = self.left_widget.video_player
        handle_player_position_changed(video_player.slider_timeline, video_player.is_slider_moving, position, self.update_time_label)

    def on_player_duration_changed(self, duration):
        video_player = self.left_widget.video_player
        handle_player_duration_changed(video_player.slider_timeline, duration, self.update_time_label)

    def update_time_label(self):
        video_player = self.left_widget.video_player
        time_str = get_formatted_time_str(video_player.player.position(), video_player.player.duration())
        video_player.lbl_time.setText(time_str)

    def on_slider_moved(self, position):
        self.left_widget.video_player.player.setPosition(position)

    def set_video_path_only(self, video_path):
        self.video_path = video_path
        self.left_widget.set_video(video_path)

    def reset_tab(self):
        self.video_path = None
        video_player = self.left_widget.video_player
        video_player.player.setSource(QUrl())
        video_player.slider_timeline.setRange(0, 0)
        video_player.slider_timeline.setValue(0)
        video_player.lbl_time.setText("00:00:00.000 / 00:00:00.000")
        video_player.btn_play_pause.setText("Play")
