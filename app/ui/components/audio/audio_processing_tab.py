
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal, QUrl

# import utils for player controls
from app.ui.components.audio.segment_manager_widget import SegmentManagerWidget
from app.ui.utils import (
    toggle_play_pause, get_formatted_time_str,
    handle_player_position_changed, handle_player_duration_changed
)

from app.ui.components.audio.player_segment_widget import PlayerSegmentWidget
from app.ui.components.audio.mute_control_widget import MuteControlWidget
from app.ui.components.audio.export_log_widget import ExportLogWidget

class AudioProcessingTab(QWidget):
    log_message = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AudioProcessingTab")

        # Main layout
        main_layout = QHBoxLayout(self)

        # Left side: Player and Segment Manager
        self.left_widget = PlayerSegmentWidget()

        # Right side: Controls and Export
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        mute_controls = MuteControlWidget()
        export_log = ExportLogWidget()
        segment_manager = SegmentManagerWidget()
        right_layout.addWidget(segment_manager)
        right_layout.addWidget(mute_controls)
        right_layout.addWidget(export_log)
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
        self.left_widget.set_video(video_path)

    def reset_tab(self):
        video_player = self.left_widget.video_player
        video_player.player.setSource(QUrl())
        video_player.slider_timeline.setRange(0, 0)
        video_player.slider_timeline.setValue(0)
        video_player.lbl_time.setText("00:00:00.000 / 00:00:00.000")
        video_player.btn_play_pause.setText("Play")
