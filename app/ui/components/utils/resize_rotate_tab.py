from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QUrl

from app.core.helpers import get_media_info
from app.ui.utils import get_formatted_time_str, toggle_play_pause, handle_player_position_changed, handle_player_duration_changed

from .left_layout_widget import LeftLayoutWidget
from .right_layout_widget import RightLayoutWidget

class ResizeRotateTab(QWidget):
    log_message = pyqtSignal(str)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.current_video_path = None
        self.worker = None # Placeholder for future backend worker
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        self.left_layout = LeftLayoutWidget(self.main_window)
        self.right_layout = RightLayoutWidget()

        main_layout.addWidget(self.left_layout, 1) # Add stretch factor
        main_layout.addWidget(self.right_layout)
        
        self.setLayout(main_layout)

    def connect_signals(self):
        # Video loading
        self.left_layout.video_source_widget.file_selected.connect(self.set_video_path)

        # Player controls
        player = self.left_layout.video_player_widget.player
        controls = self.left_layout.player_controls_widget
        
        controls.btn_play_pause.clicked.connect(lambda: toggle_play_pause(player, controls.btn_play_pause))
        #Add on 08282026
        player.positionChanged.connect(self.update_time_label)
        player.durationChanged.connect(self.update_time_label)
        controls.slider_timeline.sliderMoved.connect(player.setPosition)
        controls.btn_mute.toggled.connect(player.audioOutput().setMuted)
        controls.slider_volume.valueChanged.connect(lambda vol: player.audioOutput().setVolume(vol / 100.0))

        # Resize/Rotate controls
        self.right_layout.rotate_block.preview_rotate_requested.connect(self.on_preview_rotate)
        # self.right_layout.rotate_block.apply_rotate_requested.connect(self.on_apply_rotate) # Placeholder
        # self.right_layout.resize_block.apply_button.clicked.connect(self.on_apply_resize)   # Placeholder


    def set_video_path(self, file_path):
        self.current_video_path = file_path
        if hasattr(self.left_layout, 'video_source_widget'):
            self.left_layout.video_source_widget.set_video_path(file_path)
        
        self.log_message.emit(f"Resize/Rotate tab received video: {file_path}")
        self.left_layout.video_player_widget.load_video(file_path)
        
        try:
            info = get_media_info(file_path)
            video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
            if video_stream:
                width = int(video_stream["width"])
                height = int(video_stream["height"])
                self.right_layout.resize_block.set_original_dimensions(width, height)
        except Exception as e:
            self.log_message.emit(f"Error getting media info: {e}")

    def on_preview_rotate(self, option):
        self.left_layout.video_player_widget.apply_rotation_and_flip(option)

    def update_time_label(self):
        player = self.left_layout.video_player_widget.player
        controls = self.left_layout.player_controls_widget

        # 1. Cập nhật range và position cho thanh slider timeline
        if player.duration() > 0:
            controls.slider_timeline.blockSignals(True)
            controls.slider_timeline.setRange(0, player.duration())
            controls.slider_timeline.setValue(player.position())
            controls.slider_timeline.blockSignals(False)

        # 2. Cập nhật label thời gian (00:00:00 / 00:01:30)
        time_str = get_formatted_time_str(player.position(), player.duration())
        controls.lbl_time.setText(time_str)

    def terminate(self):
        """
        Clean up resources, especially the running worker thread.
        """
        self.log_message.emit("Terminating Resize/Rotate Tab...")
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        self.left_layout.video_player_widget.terminate()

    def cancel(self):
        """
        Cancels any ongoing operation.
        """
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log_message.emit("Resize/Rotate operation cancelled.")

    def reset_ui(self):
        """
        Resets the entire tab to its initial state.
        """
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
            self.worker = None

        self.current_video_path = None
        self.left_layout.reset_ui()
        self.right_layout.reset_ui()
