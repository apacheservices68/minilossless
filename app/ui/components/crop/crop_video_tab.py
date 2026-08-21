
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QSpinBox, QPushButton, QSizePolicy, QStackedLayout, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QRect

from app.core.helpers import get_media_info
from app.ui.utils import get_formatted_time_str, toggle_play_pause, handle_player_position_changed, handle_player_duration_changed
from app.ui.components.video_player_widget import VideoPlayerWidget
from .crop_overlay_widget import CropOverlayWidget
from .ruler_widget import RulerWidget
from .video_container import VideoContainer

class CropVideoTab(QWidget):
    log_message = pyqtSignal(str)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.video_player_widget = VideoPlayerWidget()
        self.overlay_widget = None
        self.video_container = None
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Layout (Rulers and Player)
        left_container = QWidget()
        left_grid = QGridLayout(left_container)
        left_grid.setContentsMargins(0, 0, 0, 0)
        left_grid.setSpacing(0)

        self.h_ruler = RulerWidget(Qt.Orientation.Horizontal)
        self.v_ruler = RulerWidget(Qt.Orientation.Vertical)
        
        self.video_container = VideoContainer()
        player_stack = QWidget()
        player_layout = QStackedLayout(player_stack)
        player_layout.setContentsMargins(0,0,0,0)
        player_layout.addWidget(self.video_player_widget)
        self.overlay_widget = CropOverlayWidget(player_stack)
        player_layout.addWidget(self.overlay_widget)
        self.video_container.set_video_widget(player_stack)

        left_grid.addWidget(QWidget(), 0, 0)  # Corner widget
        left_grid.addWidget(self.h_ruler, 0, 1)
        left_grid.addWidget(self.v_ruler, 1, 0)
        left_grid.addWidget(self.video_container, 1, 1)
        left_grid.addLayout(self.create_player_controls(), 2, 1) # Add player controls below


        # Right Layout (Controls)
        right_layout_widget = self.create_right_layout()

        main_layout.addWidget(left_container, 7)
        main_layout.addWidget(right_layout_widget, 3)

    def create_right_layout(self):
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 0, 10, 10)

        # Controls Group
        controls_group = QGroupBox("Controls")
        controls_layout = QGridLayout()

        # Position
        pos_group = QGroupBox("Position")
        pos_layout = QGridLayout()
        pos_layout.addWidget(QLabel("Pos X:"), 0, 0)
        self.pos_x_spinbox = QSpinBox()
        pos_layout.addWidget(self.pos_x_spinbox, 0, 1)
        pos_layout.addWidget(QLabel("Pos Y:"), 1, 0)
        self.pos_y_spinbox = QSpinBox()
        pos_layout.addWidget(self.pos_y_spinbox, 1, 1)
        pos_group.setLayout(pos_layout)

        # Size
        size_group = QGroupBox("Size")
        size_layout = QGridLayout()
        size_layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_spinbox = QSpinBox()
        size_layout.addWidget(self.width_spinbox, 0, 1)
        size_layout.addWidget(QLabel("Height:"), 1, 0)
        self.height_spinbox = QSpinBox()
        size_layout.addWidget(self.height_spinbox, 1, 1)
        size_group.setLayout(size_layout)

        controls_layout.addWidget(pos_group, 0, 0)
        controls_layout.addWidget(size_group, 1, 0)
        controls_group.setLayout(controls_layout)

        # Process Output Group
        process_group = QGroupBox("Process Output")
        process_layout = QVBoxLayout()
        self.process_button = QPushButton("Process Crop Video")
        self.process_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        process_layout.addWidget(self.process_button)
        process_group.setLayout(process_layout)

        right_layout.addWidget(controls_group)
        right_layout.addWidget(process_group)
        right_layout.addStretch()

        main_container = QWidget()
        main_container.setLayout(right_layout)
        main_container.setFixedWidth(350)

        return main_container

    def create_player_controls(self):
        # Player Controls Layout
        player_controls_layout = QHBoxLayout()
        player_controls_layout.setContentsMargins(0, 5, 0, 0)

        self.btn_play_pause = QPushButton("Play")
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.lbl_time = QLabel("00:00:00.000 / 00:00:00.000")
        
        # Mute Button (Simplified)
        self.btn_mute = QPushButton("Mute")
        self.btn_mute.setCheckable(True)

        # Volume Slider (Simplified)
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(100)
        self.slider_volume.setMaximumWidth(100)

        player_controls_layout.addWidget(self.btn_play_pause)
        player_controls_layout.addWidget(self.slider_timeline)
        player_controls_layout.addWidget(self.lbl_time)
        player_controls_layout.addWidget(self.btn_mute)
        player_controls_layout.addWidget(self.slider_volume)

        return player_controls_layout

    def connect_signals(self):
        # Crop signals
        self.overlay_widget.crop_rect_changed.connect(self.update_spinboxes_from_rect)
        self.pos_x_spinbox.valueChanged.connect(self.update_rect_from_spinboxes)
        self.pos_y_spinbox.valueChanged.connect(self.update_rect_from_spinboxes)
        self.width_spinbox.valueChanged.connect(self.update_rect_from_spinboxes)
        self.height_spinbox.valueChanged.connect(self.update_rect_from_spinboxes)

        # Player signals
        self.video_player_widget.player.positionChanged.connect(self.on_player_position_changed)
        self.video_player_widget.player.durationChanged.connect(self.on_player_duration_changed)
        self.video_player_widget.player.playbackStateChanged.connect(self.on_playback_state_changed)

        self.slider_timeline.sliderMoved.connect(self.on_slider_moved)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.btn_mute.toggled.connect(self.on_mute_toggled)
        self.slider_volume.valueChanged.connect(self.on_volume_changed)

    def update_spinboxes_from_rect(self, rect):
        self.pos_x_spinbox.blockSignals(True)
        self.pos_y_spinbox.blockSignals(True)
        self.width_spinbox.blockSignals(True)
        self.height_spinbox.blockSignals(True)

        self.pos_x_spinbox.setValue(rect.x())
        self.pos_y_spinbox.setValue(rect.y())
        self.width_spinbox.setValue(rect.width())
        self.height_spinbox.setValue(rect.height())

        self.pos_x_spinbox.blockSignals(False)
        self.pos_y_spinbox.blockSignals(False)
        self.width_spinbox.blockSignals(False)
        self.height_spinbox.blockSignals(False)

    def update_rect_from_spinboxes(self):
        rect = QRect(
            self.pos_x_spinbox.value(),
            self.pos_y_spinbox.value(),
            self.width_spinbox.value(),
            self.height_spinbox.value()
        )
        self.overlay_widget.set_crop_rect(rect)

    # --- Player Control Slots ---

    def on_playback_state_changed(self, state):
        if state == self.video_player_widget.player.PlaybackState.PlayingState:
            self.btn_play_pause.setText("Pause")
        else:
            self.btn_play_pause.setText("Play")

    def toggle_play_pause(self):
        toggle_play_pause(self.video_player_widget.player, self.btn_play_pause)

    def on_player_position_changed(self, position):
        # For now, we assume is_slider_moving is False as we don't implement the press/release logic for simplicity
        handle_player_position_changed(self.slider_timeline, False, position, self.update_time_label)

    def on_player_duration_changed(self, duration):
        handle_player_duration_changed(self.slider_timeline, duration, self.update_time_label)

    def update_time_label(self):
        time_str = get_formatted_time_str(self.video_player_widget.player.position(), self.video_player_widget.player.duration())
        self.lbl_time.setText(time_str)

    def on_slider_moved(self, position):
        self.video_player_widget.player.setPosition(position)

    def on_mute_toggled(self, checked):
        self.video_player_widget.player.audioOutput().setMuted(checked)

    def on_volume_changed(self, value):
        # QMediaPlayer volume is float 0.0-1.0
        self.video_player_widget.player.audioOutput().setVolume(value / 100.0)

    def set_video_path_only(self, file_path):
        self.log_message.emit(f"Crop tab received video: {file_path}")
        self.video_player_widget.load_video(file_path)
        try:
            info = get_media_info(file_path)
            video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
            if video_stream:
                video_width = video_stream["width"]
                video_height = video_stream["height"]
                aspect_ratio = video_width / video_height

                self.video_container.set_aspect_ratio(aspect_ratio)
                self.h_ruler.set_max_value(video_width)
                self.v_ruler.set_max_value(video_height)

                self.pos_x_spinbox.setRange(0, video_width)
                self.pos_y_spinbox.setRange(0, video_height)
                self.width_spinbox.setRange(0, video_width)
                self.height_spinbox.setRange(0, video_height)
        except Exception as e:
            self.log_message.emit(f"Error getting media info: {e}")
