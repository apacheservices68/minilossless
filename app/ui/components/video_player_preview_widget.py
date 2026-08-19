import os

import cv2
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QGroupBox,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsItem
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QPointF, QSizeF
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QPainter, QPainterPath, QFontDatabase
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem

from app.ui.utils import (
    toggle_play_pause, get_formatted_time_str,
    handle_player_position_changed, handle_player_duration_changed,
    show_close_video_help
)

class ResizableGraphicsView(QGraphicsView):
    resized = pyqtSignal()

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setStyleSheet("background: black; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()

class DraggableTextItem(QGraphicsTextItem):
    def __init__(self, text="Text", font_size=32, angle=0.0, opacity=1.0, font_family="DejaVu Sans"):
        super().__init__(text)
        self.font_size = font_size
        self.angle = angle
        self.opacity_val = opacity
        self.font_family = font_family
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        self.color_stroke = QColor("black")
        self.color_fill = QColor("white")
        self.update_style()

    def update_style(self, text=None, font_size=None, angle=None, opacity=None):
        if text is not None:
            self.setPlainText(text)
        if font_size is not None:
            self.font_size = font_size
        if angle is not None:
            self.angle = angle
        if opacity is not None:
            self.opacity_val = opacity
            self.setOpacity(self.opacity_val)

        font = QFont(self.font_family, self.font_size, QFont.Weight.Bold)
        self.setFont(font)
        self.setDefaultTextColor(self.color_fill)
        
        rect = self.boundingRect()
        self.setTransformOriginPoint(rect.width() / 2, rect.height() / 2)
        self.setRotation(self.angle)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.isSelected():
            pen = QPen(QColor("cyan"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())

        path = QPainterPath()
        font = self.font()
        path.addText(0, font.pointSize(), font, self.toPlainText())
        
        stroke_w = max(2, self.font_size // 8)
        stroke_color = QColor(self.color_stroke)
        stroke_color.setAlphaF(self.opacity_val)
        
        fill_color = QColor(self.color_fill)
        fill_color.setAlphaF(self.opacity_val)

        painter.setPen(QPen(stroke_color, stroke_w, Qt.PenStyle.SolidLine))
        painter.drawPath(path)

        painter.fillPath(path, QBrush(fill_color))

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        # Tìm widget cha (AdvanceWatermarkTab) để gọi tự động lưu
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            parent_tab = view.parent()
            
            # Duyệt ngược lên các parent widget để tìm đúng hàm trigger_auto_save
            while parent_tab and not hasattr(parent_tab, "trigger_auto_save"):
                parent_tab = parent_tab.parent()
            
            if parent_tab and hasattr(parent_tab, "trigger_auto_save"):
                parent_tab.trigger_auto_save()

class VideoPlayerPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_slider_moving = False
        self.video_w = 1280
        self.video_h = 720
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        player_group = QGroupBox("Interactive Video Player Preview (QGraphicsScene)")
        player_layout = QVBoxLayout()
        
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.video_w, self.video_h)
        self.view = ResizableGraphicsView(self.scene, self)
        self.view.setMinimumHeight(400)
        self.view.resized.connect(self.fit_video_in_view)
        
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)
        self.video_item.setZValue(0)
        self.video_item.setPos(0, 0)
        self.video_item.setSize(QSizeF(float(self.video_w), float(self.video_h)))

        player_layout.addWidget(self.view, 1)
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_item)
        
        self.player.positionChanged.connect(self.on_player_position_changed)
        self.player.durationChanged.connect(self.on_player_duration_changed)
        
        timeline_layout = QHBoxLayout()
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.slider_timeline.setRange(0, 0)
        self.slider_timeline.sliderPressed.connect(self.on_slider_pressed)
        self.slider_timeline.sliderReleased.connect(self.on_slider_released)
        self.slider_timeline.sliderMoved.connect(self.on_slider_moved)
        
        self.lbl_time = QLabel("00:00:00.000 / 00:00:00.000")
        timeline_layout.addWidget(self.slider_timeline, 1)
        timeline_layout.addWidget(self.lbl_time)
        player_layout.addLayout(timeline_layout)
        
        media_controls = QHBoxLayout()
        self.btn_play_pause = QPushButton("Play")
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        media_controls.addWidget(self.btn_play_pause)
        
        self.btn_help_close = QPushButton("?")
        self.btn_help_close.setFixedWidth(28)
        self.btn_help_close.setToolTip("Nhấn Ctrl + W (Windows/Linux) hoặc Cmd + W (macOS) để đóng video hiện tại.")
        self.btn_help_close.clicked.connect(lambda: show_close_video_help(self))
        media_controls.addWidget(self.btn_help_close)
        
        player_layout.addLayout(media_controls)
        
        player_group.setLayout(player_layout)
        layout.addWidget(player_group)

    def fit_video_in_view(self):
        if hasattr(self, 'video_w') and self.video_w > 0:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_video(self, path):
        if not path or not os.path.exists(path):
            return

        self.selected_video_path = path
        self.player.setSource(QUrl.fromLocalFile(path))

        # 1. Đọc đúng kích thước thực của Video bằng OpenCV
        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            self.video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
        else:
            self.video_w, self.video_h = 1280, 720

        # 2. Khóa cứng SceneRect và video_item đúng chuẩn Pixel của Video
        self.scene.setSceneRect(0, 0, self.video_w, self.video_h)
        self.video_item.setPos(0, 0)
        self.video_item.setSize(QSizeF(float(self.video_w), float(self.video_h)))

        # 3. Fit khung hiển thị Viewport
        self.fit_video_in_view()

    def reset_video(self):
        self.player.setSource(QUrl())
        self.slider_timeline.setRange(0, 0)
        self.slider_timeline.setValue(0)
        self.lbl_time.setText("00:00:00.000 / 00:00:00.000")
        self.btn_play_pause.setText("Play")
        self.video_w, self.video_h = 1280, 720
        self.scene.setSceneRect(0, 0, 1280, 720)
        self.video_item.setSize(QSizeF(1280.0, 720.0))
        self.fit_video_in_view()
        # Add on 08172026 | fix bug clear drawtext after cltr+w on advanced_watermark_tab
        for item in self.scene.items():
            if item != self.video_item:
                try:
                    self.scene.removeItem(item)
                except Exception:
                    pass

    def toggle_play_pause(self):
        toggle_play_pause(self.player, self.btn_play_pause)

    def on_player_position_changed(self, position):
        handle_player_position_changed(self.slider_timeline, self.is_slider_moving, position, self.update_time_label)

    def on_player_duration_changed(self, duration):
        handle_player_duration_changed(self.slider_timeline, duration, self.update_time_label)

    def update_time_label(self):
        time_str = get_formatted_time_str(self.player.position(), self.player.duration())
        self.lbl_time.setText(time_str)

    def on_slider_pressed(self):
        self.is_slider_moving = True

    def on_slider_released(self):
        self.is_slider_moving = False
        self.player.setPosition(self.slider_timeline.value())

    def on_slider_moved(self, position):
        self.player.setPosition(position)