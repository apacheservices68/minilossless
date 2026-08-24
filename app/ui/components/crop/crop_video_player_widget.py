from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSlider, QLabel, QPushButton, QGraphicsView, QGraphicsScene, QFrame
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtCore import Qt, QUrl, QSizeF

class CropVideoPlayerWidget(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__()
        self.main_window = main_window
        self.is_slider_moving = False
        self.init_ui()

    def init_ui(self):
        player_group = QGroupBox("Video Player")
        player_layout = QVBoxLayout()

        # --- QGraphicsView setup ---
        self.scene = QGraphicsScene(self)
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)

        self.view = QGraphicsView(self.scene)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        # Sửa StyleSheet để xóa hẳn viền và nền của View
        self.view.setStyleSheet("QGraphicsView { background: transparent; border: none; padding: 0px; margin: 0px; }")
        
        # Tắt Scrollbar
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # --- End QGraphicsView setup ---

        player_layout.addWidget(self.view, 1)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_item)

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

        # Connect signals
        self.btn_mute.toggled.connect(self.on_mute_toggled)
        self.slider_volume.valueChanged.connect(self.on_volume_changed)

    # def fit_in_view(self):
    #     self.view.fitInView(self.video_item, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_in_view() # Keep video centered and scaled on resize

    def on_mute_toggled(self, is_muted):
        self.audio_output.setMuted(is_muted)
        self.btn_mute.setText("🔇" if is_muted else "🔈")

    def on_volume_changed(self, value):
        self.audio_output.setVolume(value / 100.0)

    def on_slider_pressed(self):
        self.is_slider_moving = True

    def on_slider_released(self):
        self.is_slider_moving = False
        self.player.setPosition(self.slider_timeline.value())

    def on_slider_moved(self, position):
        self.player.setPosition(position)

    def load_video(self, video_path):
        if video_path:
            self.player.setSource(QUrl.fromLocalFile(video_path))
            # The video item needs to be manually sized to the video's resolution
            self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def fit_in_view(self):
        if self.video_item and not self.video_item.boundingRect().isEmpty():
            rect = self.video_item.boundingRect()
            self.scene.setSceneRect(rect)
            # Ép video lấp đầy Viewport, hoàn toàn triệt tiêu viền đen
            self.view.fitInView(rect, Qt.AspectRatioMode.IgnoreAspectRatio)

    def _on_media_status_changed(self, status):
        # Đợi media load xong hoàn toàn (BufferedMedia hoặc LoadedMedia)
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            size = self.player.videoSink().videoSize()
            if not size.isEmpty():
                self.video_item.setPos(0, 0)
                self.video_item.setSize(QSizeF(size))
                self.scene.setSceneRect(0, 0, size.width(), size.height())
                # Delay nhẹ 50ms cho GraphicsEngine cập nhật geometry rồi fit view
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(50, self.fit_in_view)

    def reset_player(self):
        self.player.stop()
        self.player.setSource(QUrl())
        self.slider_timeline.setValue(0)
        self.lbl_time.setText("00:00:00.000 / 00:00:00.000")
        self.btn_play_pause.setText("Play")