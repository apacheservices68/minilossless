import os

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QSpinBox, QPushButton, QSizePolicy, QStackedLayout, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QRect

from app.core.helpers import get_media_info
from app.services.crop_worker import CropWorker
from app.ui.components.crop.player_control_widget import PlayerControlsWidget
from app.ui.components.video_source_widget import VideoSourceWidget
from app.ui.utils import get_formatted_time_str, toggle_play_pause, handle_player_position_changed, handle_player_duration_changed
from app.ui.components.crop.crop_video_player_widget import CropVideoPlayerWidget
from .crop_overlay_widget import CropOverlayWidget
from .ruler_widget import RulerWidget
from .video_container import VideoContainer
from .right_layout_widget import RightLayoutWidget

class CropVideoTab(QWidget):
    log_message = pyqtSignal(str)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        # self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.main_window = main_window
        self.video_player_widget = CropVideoPlayerWidget()
        self.overlay_widget = None
        self.video_container = None
        self.controls_widget = None
        self.right_layout = None

        self.current_video_path = None
        self.crop_worker = None
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Layout (Rulers and Player)
        left_container = QWidget()
        left_grid = QGridLayout(left_container)
        main_layout.setContentsMargins(5, 5, 5, 5)
        left_grid.setSpacing(0)
        left_grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # --- 1. THÊM VIDEO SOURCE WIDGET VÀO ĐÂY ---
        self.video_source_widget = VideoSourceWidget(self)
        self.video_source_widget.file_selected.connect(self.main_window.set_active_video)
        # Đưa VideoSourceWidget vào cột 1 (chiếm 2 cột từ 0 đến 1) ở hàng 0
        left_grid.addWidget(self.video_source_widget, 0, 0, 1, 2)

        self.h_ruler = RulerWidget(Qt.Orientation.Horizontal)
        self.v_ruler = RulerWidget(Qt.Orientation.Vertical)

        # Container for the video player and overlay
        self.video_container = VideoContainer()
        self.overlay_widget = CropOverlayWidget()
        self.overlay_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.video_container.set_video_widget(self.video_player_widget.view, self.overlay_widget)

        # Add các widget vào Grid chuẩn vị trí
        left_grid.addWidget(QWidget(), 1, 0)  # Corner widget (hàng 1)
        left_grid.addWidget(self.h_ruler, 1, 1) # (hàng 1)
        left_grid.addWidget(self.v_ruler, 2, 0) # (hàng 2)
        left_grid.addWidget(self.video_container, 2, 1) # (hàng 2)

        # Initialize separate controls widget
        self.player_controls = PlayerControlsWidget()

        # Add to left_grid in row 2
        left_grid.addWidget(self.player_controls, 3, 1)

        # Set row stretch factors to prioritize video expansion
        left_grid.setRowStretch(2, 1)  # Cập nhật stretch cho row 2 chứa video container
        left_grid.setRowStretch(3, 0)

        # Right Layout (Controls)
        self.right_layout = RightLayoutWidget()

        main_layout.addWidget(left_container, 7)
        main_layout.addWidget(self.right_layout, 3)

    def connect_signals(self):
        # Crop signals
        self.overlay_widget.crop_rect_changed.connect(self.update_spinboxes_from_rect)
        self.right_layout.pos_x_spinbox.valueChanged.connect(self.update_rect_from_spinboxes)
        self.right_layout.pos_y_spinbox.valueChanged.connect(self.update_rect_from_spinboxes)
        self.right_layout.width_spinbox.valueChanged.connect(self.update_rect_from_spinboxes)
        self.right_layout.height_spinbox.valueChanged.connect(self.update_rect_from_spinboxes)

        # Player signals
        self.video_player_widget.player.positionChanged.connect(self.on_player_position_changed)
        self.video_player_widget.player.durationChanged.connect(self.on_player_duration_changed)
        self.video_player_widget.player.playbackStateChanged.connect(self.on_playback_state_changed)

        self.player_controls.slider_timeline.sliderMoved.connect(self.on_slider_moved)
        self.player_controls.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.player_controls.btn_mute.toggled.connect(self.on_mute_toggled)
        self.player_controls.slider_volume.valueChanged.connect(self.on_volume_changed)

        # Connect event Reset button
        self.right_layout.reset_button.clicked.connect(self.reset_crop_to_default)
        self.right_layout.process_button.clicked.connect(self.start_crop_process)

    def start_crop_process(self):
        if not self.current_video_path or not os.path.exists(self.current_video_path):
            self.log_message.emit("Error: No valid video loaded to crop.")
            return

        # 1. Lấy thông số crop từ các SpinBox
        x = self.right_layout.pos_x_spinbox.value()
        y = self.right_layout.pos_y_spinbox.value()
        w = self.right_layout.width_spinbox.value()
        h = self.right_layout.height_spinbox.value()

        if w <= 0 or h <= 0:
            self.log_message.emit("Error: Crop width and height must be greater than 0.")
            return

        # 2. Tạo đường dẫn file đầu ra (Thêm hậu tố _cropped)
        folder, filename = os.path.split(self.current_video_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(folder, f"{name}_cropped{ext}")

        # 3. Lấy thời lượng video (để tính %)
        duration_sec = self.video_player_widget.player.duration() / 1000.0

        # 4. Khóa nút để tránh bấm dồn dập
        self.right_layout.process_button.setEnabled(False)
        self.right_layout.process_button.setText("Processing...")

        # 5. Khởi tạo và chạy Worker
        self.crop_worker = CropWorker(
            input_path=self.current_video_path,
            output_path=output_path,
            x=x, y=y, w=w, h=h,
            duration_sec=duration_sec
        )

        # Nối các tín hiệu từ Worker
        self.crop_worker.log_signal.connect(self.log_message.emit)
        self.crop_worker.progress.connect(self.on_crop_progress)
        self.crop_worker.finished_signal.connect(self.on_crop_finished)

        self.crop_worker.start()

    def on_crop_progress(self, percent):
        # Cập nhật phần trăm lên nút bấm hoặc Log
        self.right_layout.process_button.setText(f"Processing... {percent}%")

    def on_crop_finished(self, success, result_message):
        # Mở lại nút bấm
        self.right_layout.process_button.setEnabled(True)
        self.right_layout.process_button.setText("Process Crop Video")

        if success:
            self.log_message.emit(f"SUCCESS: Cropped video saved to: {result_message}")
        else:
            self.log_message.emit(f"ERROR: Crop process failed: {result_message}")
        
        self.crop_worker = None

    def reset_crop_to_default(self):
        # Lấy độ phân giải video thực tế từ overlay_widget
        video_width = self.overlay_widget.video_width
        video_height = self.overlay_widget.video_height

        if video_width > 1 and video_height > 1:
            # Tính toán lại khung Crop mặc định = 60% kích thước video ở chính giữa
            crop_w = int(video_width * 0.6)
            crop_h = int(video_height * 0.6)
            crop_x = int((video_width - crop_w) / 2)
            crop_y = int((video_height - crop_h) / 2)
            default_rect = QRect(crop_x, crop_y, crop_w, crop_h)

            # Đặt lại vị trí overlay và đồng bộ 4 ô SpinBox nhập liệu
            self.overlay_widget.set_crop_rect(default_rect)
            self.update_spinboxes_from_rect(default_rect)
            self.log_message.emit("Crop rectangle reset to default.")

    def update_spinboxes_from_rect(self, rect):
        self.right_layout.pos_x_spinbox.blockSignals(True)
        self.right_layout.pos_y_spinbox.blockSignals(True)
        self.right_layout.width_spinbox.blockSignals(True)
        self.right_layout.height_spinbox.blockSignals(True)

        self.right_layout.pos_x_spinbox.setValue(rect.x())
        self.right_layout.pos_y_spinbox.setValue(rect.y())
        self.right_layout.width_spinbox.setValue(rect.width())
        self.right_layout.height_spinbox.setValue(rect.height())

        self.right_layout.pos_x_spinbox.blockSignals(False)
        self.right_layout.pos_y_spinbox.blockSignals(False)
        self.right_layout.width_spinbox.blockSignals(False)
        self.right_layout.height_spinbox.blockSignals(False)

    def update_rect_from_spinboxes(self):
        rect = QRect(
            self.right_layout.pos_x_spinbox.value(),
            self.right_layout.pos_y_spinbox.value(),
            self.right_layout.width_spinbox.value(),
            self.right_layout.height_spinbox.value()
        )
        self.overlay_widget.set_crop_rect(rect)

    # --- Player Control Slots ---

    def on_playback_state_changed(self, state):
        if state == self.video_player_widget.player.PlaybackState.PlayingState:
            self.player_controls.btn_play_pause.setText("Pause")
        else:
            self.player_controls.btn_play_pause.setText("Play")

    def toggle_play_pause(self):
        toggle_play_pause(self.video_player_widget.player, self.player_controls.btn_play_pause)

    def on_player_position_changed(self, position):
        # For now, we assume is_slider_moving is False as we don't implement the press/release logic for simplicity
        handle_player_position_changed(self.player_controls.slider_timeline, False, position, self.update_time_label)

    def on_player_duration_changed(self, duration):
        handle_player_duration_changed(self.player_controls.slider_timeline, duration, self.update_time_label)

    def update_time_label(self):
        time_str = get_formatted_time_str(self.video_player_widget.player.position(), self.video_player_widget.player.duration())
        self.player_controls.lbl_time.setText(time_str)

    def on_slider_moved(self, position):
        self.video_player_widget.player.setPosition(position)

    def on_mute_toggled(self, checked):
        self.video_player_widget.player.audioOutput().setMuted(checked)

    def on_volume_changed(self, value):
        # QMediaPlayer volume is float 0.0-1.0
        self.video_player_widget.player.audioOutput().setVolume(value / 100.0)


    def set_video_path_only(self, file_path):
        self.current_video_path = file_path
        if hasattr(self, 'video_source_widget'):
            self.video_source_widget.set_video_path(file_path)
        self.log_message.emit(f"Crop tab received video: {file_path}")
        self.video_player_widget.load_video(file_path)
        try:
            info = get_media_info(file_path)
            video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
            if video_stream:
                video_width = int(video_stream["width"])
                video_height = int(video_stream["height"])
                aspect_ratio = video_width / float(video_height)

                self.overlay_widget.set_video_resolution(video_width, video_height)

                self.video_container.set_h_ruler(self.h_ruler)
                self.video_container.set_v_ruler(self.v_ruler)
                self.video_container.set_aspect_ratio(aspect_ratio)

                self.h_ruler.set_max_value(video_width)
                self.v_ruler.set_max_value(video_height)

                self.right_layout.pos_x_spinbox.setRange(0, video_width)
                self.right_layout.pos_y_spinbox.setRange(0, video_height)
                self.right_layout.width_spinbox.setRange(0, video_width)
                self.right_layout.height_spinbox.setRange(0, video_height)

                # Set initial crop rectangle to the full video size
                # self.overlay_widget.set_crop_rect(QRect(0, 0, video_width, video_height))
                # Mặc định tạo khung crop bằng 60% kích thước video ở chính giữa
                crop_w = int(video_width * 0.6)
                crop_h = int(video_height * 0.6)
                crop_x = int((video_width - crop_w) / 2)
                crop_y = int((video_height - crop_h) / 2)
                initial_rect = QRect(crop_x, crop_y, crop_w, crop_h)

                self.overlay_widget.set_crop_rect(initial_rect)
                self.update_spinboxes_from_rect(initial_rect)

        except Exception as e:
            self.log_message.emit(f"Error getting media info: {e}")

    def reset_ui(self):
        if self.crop_worker and self.crop_worker.isRunning():
            self.crop_worker.cancel()
            self.crop_worker.wait()
            self.crop_worker = None
        # self.video_path = None
        self.current_video_path = None
        # Reset VideoSourceWidget
        if hasattr(self, 'video_source_widget'):
            self.video_source_widget.set_video_path("")
        self.video_player_widget.reset_player()
        self.overlay_widget.reset_ui()
        self.right_layout.reset_ui()
        self.player_controls.reset_ui()
        self.video_container.reset_ui()
