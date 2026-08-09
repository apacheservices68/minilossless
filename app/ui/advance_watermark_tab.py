import math
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QSlider, QCheckBox, QSpinBox, QListWidget, QListWidgetItem, QGroupBox,
    QFormLayout, QMessageBox, QProgressBar, QFileDialog,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsItem,
    QComboBox
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QThread, QPointF, QSizeF
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QPainter, QPainterPath, QFontDatabase
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem

from app.services.ai_processor import AIProcessorSignals
from app.services.ffmpeg_service import process_video_ai


class ResizableGraphicsView(QGraphicsView):
    """View tự động scale Video + Text vừa vặn khung hình khi resize window"""
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
    """Text Item hỗ trợ Kéo thả + Xoay + Opacity + Font trên QGraphicsScene"""
    def __init__(self, text="Text", font_size=32, angle=0.0, opacity=1.0, font_family="DejaVu Sans"):
        super().__init__(text)
        self.font_size = font_size
        self.angle = angle
        self.opacity_val = opacity
        self.font_family = font_family # <-- LƯU FONT FAMILY
        
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

        # DÙNG FONT FAMILY ĐƯỢC TRUYỀN VÀO
        font = QFont(self.font_family, self.font_size, QFont.Weight.Bold)
        self.setFont(font)
        self.setDefaultTextColor(self.color_fill)
        
        rect = self.boundingRect()
        self.setTransformOriginPoint(rect.width() / 2, rect.height() / 2)
        self.setRotation(self.angle)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Border khi chọn
        if self.isSelected():
            pen = QPen(QColor("cyan"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())

        # Outline Stroke Text
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

        # Inner Fill
        painter.fillPath(path, QBrush(fill_color))


class AIProcessWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, input_path, output_path, texts, use_cuda, face_blur, face_blur_pct, face_blur_type, face_blur_image_path, bg_blur, bg_blur_strength, face_blur_style="Gaussian", face_blur_strength=15):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.texts = texts
        self.use_cuda = use_cuda
        self.face_blur = face_blur
        self.face_blur_pct = face_blur_pct
        self.face_blur_type = face_blur_type
        self.face_blur_image_path = face_blur_image_path
        self.bg_blur = bg_blur
        self.bg_blur_strength = bg_blur_strength
        self.face_blur_style = face_blur_style
        self.face_blur_strength = face_blur_strength

    def run(self):
        signals = AIProcessorSignals()
        signals.progress.connect(self.progress.emit)
        signals.finished.connect(self.finished.emit)
        try:
            process_video_ai(
                input_video_path=self.input_path,
                output_video_path=self.output_path,
                texts=self.texts,
                use_cuda=self.use_cuda,
                face_blur_enabled=self.face_blur,
                face_blur_pct=self.face_blur_pct,
                face_blur_type=self.face_blur_type,
                face_blur_image_path=self.face_blur_image_path,
                face_blur_style=self.face_blur_style,
                face_blur_strength=self.face_blur_strength,
                bg_blur_enabled=self.bg_blur,
                bg_blur_strength=self.bg_blur_strength,
                signals=signals
            )
        except Exception as e:
            self.finished.emit(False, str(e))


class AdvanceWatermarkTab(QWidget):
    log_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. Register file font từ thư mục dự án
        font_path = "assets/fonts/DejaVuSans-Bold.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        
        if font_id != -1:
            # Lấy tên Font Family đã register thành công
            self.app_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            # Fallback nếu không thấy file font
            self.app_font_family = "DejaVu Sans"
        self.selected_video_path = ""
        self.text_items = []
        self.selected_item = None
        self.is_slider_moving = False
        
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left Panel
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 3)
        
        player_group = QGroupBox("Interactive Video Player Preview (QGraphicsScene)")
        player_layout = QVBoxLayout()
        
        self.scene = QGraphicsScene(self)
        self.view = ResizableGraphicsView(self.scene, self)
        self.view.setMinimumHeight(400)
        self.view.resized.connect(self.fit_video_in_view)
        
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)
        self.video_item.setZValue(0)
        
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
        
        # Trợ giúp trực quan để đóng video
        self.btn_help_close = QPushButton("?")
        self.btn_help_close.setFixedWidth(28)
        self.btn_help_close.setToolTip("Nhấn Ctrl + W (Windows/Linux) hoặc Cmd + W (macOS) để đóng video hiện tại.")
        self.btn_help_close.clicked.connect(lambda: QMessageBox.information(self, "Trợ giúp", "Nhấn Ctrl + W (Windows/Linux) hoặc Cmd + W (macOS) để đóng video hiện tại."))
        media_controls.addWidget(self.btn_help_close)
        
        player_layout.addLayout(media_controls)
        
        player_group.setLayout(player_layout)
        left_layout.addWidget(player_group)
        
        # Right Panel
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 2)
        
        text_group = QGroupBox("Canva-Style Multi-Text Overlays")
        text_layout = QVBoxLayout()
        
        edit_form = QFormLayout()
        self.txt_overlay_text = QLineEdit("My Watermark")
        self.txt_overlay_text.textChanged.connect(self.on_control_properties_changed)
        
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 200)
        self.spin_font_size.setValue(32)
        self.spin_font_size.valueChanged.connect(self.on_control_properties_changed)
        
        self.slider_rotation = QSlider(Qt.Orientation.Horizontal)
        self.slider_rotation.setRange(-360, 360)
        self.slider_rotation.setValue(0)
        self.slider_rotation.valueChanged.connect(self.on_control_properties_changed)
        
        # THÊM OPTION OPACITY (ĐỘ MỜ)
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(100)
        self.slider_opacity.valueChanged.connect(self.on_control_properties_changed)
        
        edit_form.addRow("Text Content:", self.txt_overlay_text)
        edit_form.addRow("Font Size (px):", self.spin_font_size)
        edit_form.addRow("Rotation Angle (°):", self.slider_rotation)
        edit_form.addRow("Opacity (%):", self.slider_opacity)
        text_layout.addLayout(edit_form)
        
        self.list_overlays = QListWidget()
        self.list_overlays.currentRowChanged.connect(self.on_list_selection_changed)
        text_layout.addWidget(self.list_overlays)
        
        buttons_layout = QHBoxLayout()
        btn_add_text = QPushButton("Add New Text Overlay")
        btn_add_text.setStyleSheet("background-color: #008CBA; color: white;")
        btn_add_text.clicked.connect(self.add_new_text_overlay)
        
        btn_delete_text = QPushButton("Delete Selected Text")
        btn_delete_text.setStyleSheet("background-color: #f44336; color: white;")
        btn_delete_text.clicked.connect(self.delete_selected_text)
        
        buttons_layout.addWidget(btn_add_text)
        buttons_layout.addWidget(btn_delete_text)
        text_layout.addLayout(buttons_layout)
        
        text_group.setLayout(text_layout)
        right_layout.addWidget(text_group)
        
        ai_group = QGroupBox("AI Filters & Hardware Acceleration")
        ai_layout = QFormLayout()
        
        self.chk_cuda = QCheckBox("Enable CUDA Hardware Acceleration")
        
        self.chk_face_blur = QCheckBox("Face Blur (Blur mặt)")
        self.spin_face_blur_pct = QSpinBox()
        self.spin_face_blur_pct.setRange(0, 100)
        self.spin_face_blur_pct.setValue(0)
        self.spin_face_blur_pct.setSuffix(" % top portion")
        
        self.cb_face_blur_type = QComboBox()
        self.cb_face_blur_type.addItem("Square (Hình vuông)", "Square")
        self.cb_face_blur_type.addItem("Circle/Ellipse (Hình elip)", "Ellipse")
        self.cb_face_blur_type.addItem("Replace with Image (Thay thế bằng ảnh)", "Image")
        self.cb_face_blur_type.currentIndexChanged.connect(self.on_face_blur_type_changed)
        
        self.cb_face_blur_style = QComboBox()
        self.cb_face_blur_style.addItem("Gaussian (Làm mờ mịn)", "Gaussian")
        self.cb_face_blur_style.addItem("Pixelate (Mô-sắc/Pixel)", "Pixel")
        self.cb_face_blur_style.addItem("Box Blur (Làm mờ hộp)", "Box")
        self.cb_face_blur_style.addItem("Blackout (Màu đặc)", "Blackout")
        
        self.spin_face_blur_strength = QSpinBox()
        self.spin_face_blur_strength.setRange(1, 100)
        self.spin_face_blur_strength.setValue(15)
        
        self.widget_face_image = QWidget()
        face_img_layout = QHBoxLayout(self.widget_face_image)
        face_img_layout.setContentsMargins(0, 0, 0, 0)
        self.txt_face_image_path = QLineEdit()
        self.txt_face_image_path.setPlaceholderText("Select replacement image...")
        self.btn_face_image_browse = QPushButton("Browse...")
        self.btn_face_image_browse.clicked.connect(self.browse_face_replacement_image)
        face_img_layout.addWidget(self.txt_face_image_path, 1)
        face_img_layout.addWidget(self.btn_face_image_browse)
        self.widget_face_image.setVisible(False)
        
        self.chk_bg_blur = QCheckBox("Background Blur (Xóa phông)")
        self.spin_bg_strength = QSpinBox()
        self.spin_bg_strength.setRange(1, 499)
        self.spin_bg_strength.setSingleStep(2)
        self.spin_bg_strength.setValue(101)
        self.spin_bg_strength.setSuffix(" px kernel")
        
        ai_layout.addRow(self.chk_cuda)
        ai_layout.addRow(self.chk_face_blur, self.spin_face_blur_pct)
        ai_layout.addRow("Shape/Replace Type:", self.cb_face_blur_type)
        ai_layout.addRow("Blur Style:", self.cb_face_blur_style)
        ai_layout.addRow("Blur Strength / Pixel Size:", self.spin_face_blur_strength)
        ai_layout.addRow("Replacement Image:", self.widget_face_image)
        ai_layout.addRow(self.chk_bg_blur, self.spin_bg_strength)
        ai_group.setLayout(ai_layout)
        right_layout.addWidget(ai_group)
        
        # Connect automatic saving on value change
        self.chk_cuda.stateChanged.connect(self.trigger_auto_save)
        self.chk_face_blur.stateChanged.connect(self.trigger_auto_save)
        self.spin_face_blur_pct.valueChanged.connect(self.trigger_auto_save)
        self.cb_face_blur_type.currentIndexChanged.connect(self.trigger_auto_save)
        self.cb_face_blur_style.currentIndexChanged.connect(self.trigger_auto_save)
        self.spin_face_blur_strength.valueChanged.connect(self.trigger_auto_save)
        self.chk_bg_blur.stateChanged.connect(self.trigger_auto_save)
        self.spin_bg_strength.valueChanged.connect(self.trigger_auto_save)
        
        process_group = QGroupBox("Export & Process Pipeline")
        process_layout = QVBoxLayout()
        
        self.btn_start_process = QPushButton("🚀 Run AI Export Pipeline (Re-encode)")
        self.btn_start_process.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px; padding: 10px;")
        self.btn_start_process.clicked.connect(self.start_ai_processing)
        process_layout.addWidget(self.btn_start_process)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Progress: %p%")
        process_layout.addWidget(self.progress_bar)
        
        self.lbl_progress_status = QLabel("Idle")
        self.lbl_progress_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        process_layout.addWidget(self.lbl_progress_status)
        
        process_group.setLayout(process_layout)
        right_layout.addWidget(process_group)

        self.scene.selectionChanged.connect(self.on_scene_selection_changed)

    def on_face_blur_type_changed(self):
        is_image = (self.cb_face_blur_type.currentData() == "Image")
        self.widget_face_image.setVisible(is_image)

    def trigger_auto_save(self):
        main_win = self.window()
        if hasattr(main_win, "save_project_state"):
            main_win.save_project_state()

    def browse_face_replacement_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Replacement Image", "", "Image Files (*.png *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.txt_face_image_path.setText(file_path)
            self.trigger_auto_save()

    def reset_tab(self):
        self.selected_video_path = ""
        self.player.setSource(QUrl())
        self.slider_timeline.setRange(0, 0)
        self.slider_timeline.setValue(0)
        self.lbl_time.setText("00:00:00.000 / 00:00:00.000")
        self.btn_play_pause.setText("Play")
        
        # Clear text items
        for item in self.text_items:
            try:
                self.scene.removeItem(item)
            except Exception:
                pass
        self.text_items.clear()
        self.list_overlays.clear()
        self.selected_item = None
        
        # Reset scene/video item sizes
        self.video_w, self.video_h = 1280, 720
        self.scene.setSceneRect(0, 0, 1280, 720)
        self.video_item.setPos(0, 0)
        self.video_item.setSize(QSizeF(1280.0, 720.0))
        self.fit_video_in_view()

    def fit_video_in_view(self):
        """Dùng fitInView native của PyQt để giữ nguyên 100% Aspect Ratio & Resolution"""
        if hasattr(self, 'video_w') and self.video_w > 0:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_video_path_only(self, path):
        self.selected_video_path = path
        self.player.setSource(QUrl.fromLocalFile(path))
        
        # 1. Đọc kích thước video gốc
        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            self.video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
        else:
            self.video_w, self.video_h = 1280, 720

        # 2. KHÓA CỨNG SceneRect theo đúng Pixel thực của Video
        self.scene.setSceneRect(0, 0, self.video_w, self.video_h)
        self.video_item.setPos(0, 0)
        self.video_item.setSize(QSizeF(float(self.video_w), float(self.video_h)))
        
        for item in self.text_items:
            try:
                self.scene.removeItem(item)
            except Exception:
                pass
        self.text_items.clear()
        self.list_overlays.clear()
        self.selected_item = None
        
        # 3. Fit khung hiển thị Viewport
        self.fit_video_in_view()

    def set_video_path(self, path):
        self.set_video_path_only(path)

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play_pause.setText("Play")
        else:
            self.player.play()
            self.btn_play_pause.setText("Pause")

    def on_player_position_changed(self, position):
        if not self.is_slider_moving:
            self.slider_timeline.setValue(position)
        self.update_time_label()

    def on_player_duration_changed(self, duration):
        self.slider_timeline.setRange(0, duration)
        self.update_time_label()

    def update_time_label(self):
        from app.services.ffmpeg_service import format_seconds_to_time
        pos_sec = self.player.position() / 1000.0
        dur_sec = self.player.duration() / 1000.0
        pos_str = format_seconds_to_time(pos_sec)
        dur_str = format_seconds_to_time(dur_sec)
        self.lbl_time.setText(f"{pos_str} / {dur_str}")

    def on_slider_pressed(self):
        self.is_slider_moving = True

    def on_slider_released(self):
        self.is_slider_moving = False
        self.player.setPosition(self.slider_timeline.value())

    def on_slider_moved(self, position):
        self.player.setPosition(position)

    def add_new_text_overlay(self):
        text_val = f"Text {len(self.text_items) + 1}"
        # TRUYỀN self.app_font_family VÀO ĐÂY:
        item = DraggableTextItem(text=text_val, font_size=32, angle=0.0, opacity=1.0, font_family=self.app_font_family)
        
        item.setZValue(100 + len(self.text_items))
        item.setPos(50 + len(self.text_items) * 15, 50 + len(self.text_items) * 15)
        
        self.scene.addItem(item)
        self.text_items.append(item)
        
        list_item = QListWidgetItem(text_val)
        self.list_overlays.addItem(list_item)
        
        self.list_overlays.setCurrentRow(len(self.text_items) - 1)
        item.setSelected(True)
        self.log_message.emit(f"Added text overlay: '{text_val}'")
        
        main_win = self.window()
        if hasattr(main_win, "save_project_state"):
            main_win.save_project_state()

    def delete_selected_text(self):
        if not self.selected_item:
            QMessageBox.warning(self, "Warning", "Please select a text overlay to delete first.")
            return
            
        idx = self.text_items.index(self.selected_item)
        self.text_items.pop(idx)
        self.list_overlays.takeItem(idx)
        
        self.scene.removeItem(self.selected_item)
        self.selected_item = None
        self.log_message.emit("Deleted selected text overlay.")
        
        main_win = self.window()
        if hasattr(main_win, "save_project_state"):
            main_win.save_project_state()

    def on_scene_selection_changed(self):
        selected = self.scene.selectedItems()
        text_selected = [i for i in selected if isinstance(i, DraggableTextItem)]
        
        if text_selected:
            item = text_selected[0]
            self.selected_item = item
            
            self.txt_overlay_text.blockSignals(True)
            self.spin_font_size.blockSignals(True)
            self.slider_rotation.blockSignals(True)
            self.slider_opacity.blockSignals(True)
            
            self.txt_overlay_text.setText(item.toPlainText())
            self.spin_font_size.setValue(item.font_size)
            self.slider_rotation.setValue(int(item.angle))
            self.slider_opacity.setValue(int(item.opacity_val * 100))
            
            self.txt_overlay_text.blockSignals(False)
            self.spin_font_size.blockSignals(False)
            self.slider_rotation.blockSignals(False)
            self.slider_opacity.blockSignals(False)
            
            if item in self.text_items:
                idx = self.text_items.index(item)
                self.list_overlays.setCurrentRow(idx)

    def on_list_selection_changed(self, row):
        if 0 <= row < len(self.text_items):
            item = self.text_items[row]
            self.scene.clearSelection()
            item.setSelected(True)

    def on_control_properties_changed(self):
        if self.selected_item:
            text = self.txt_overlay_text.text()
            font_size = self.spin_font_size.value()
            angle = float(self.slider_rotation.value())
            opacity = self.slider_opacity.value() / 100.0
            
            self.selected_item.update_style(text, font_size, angle, opacity)
            
            idx = self.text_items.index(self.selected_item)
            self.list_overlays.item(idx).setText(text)
            
            main_win = self.window()
            if hasattr(main_win, "save_project_state"):
                main_win.save_project_state()

    def start_ai_processing(self):
        if not self.selected_video_path:
            QMessageBox.warning(self, "Warning", "Please load a video from the main interface first.")
            return
            
        cap = cv2.VideoCapture(self.selected_video_path)
        if not cap.isOpened():
            QMessageBox.critical(self, "Error", "Cannot open loaded video.")
            return
        video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        item_rect = self.video_item.boundingRect()
        v_w = max(1.0, item_rect.width())
        v_h = max(1.0, item_rect.height())

        v_diag = math.hypot(v_w, v_h)

        texts_to_backend = []
        for item in self.text_items:
            scene_center = item.mapToItem(self.video_item, item.boundingRect().center())
            rel_center_x = scene_center.x() / v_w
            rel_center_y = scene_center.y() / v_h
            
            # CHỈNH CHỖ NÀY: Chia cho v_diag thay vì v_h
            rel_font_size = item.font_size / v_diag

            texts_to_backend.append({
                "text": item.toPlainText(),
                "rel_center_x": rel_center_x,
                "rel_center_y": rel_center_y,
                "rel_font_size": rel_font_size,
                "rotation_angle": item.angle,
                "opacity": item.opacity_val
            })

        ext = os.path.splitext(self.selected_video_path)[1]
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save AI Exported Video As", f"ai_output{ext}", f"Video Files (*{ext});;All Files (*)"
        )
        if not output_path:
            return

        # ... (Các dòng confirm dialog & worker bên dưới giữ nguyên)

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("Confirm AI Export Configuration")
        msg_box.setText("Are you sure you want to export the video with selected configurations?")
        
        cuda_status = "Enabled" if self.chk_cuda.isChecked() else "Disabled"
        face_type_str = self.cb_face_blur_type.currentText()
        if self.cb_face_blur_type.currentData() == "Image":
            face_type_str += f" ({os.path.basename(self.txt_face_image_path.text())})"
        face_style_str = self.cb_face_blur_style.currentText()
        face_strength = self.spin_face_blur_strength.value()
        fblur_status = f"Enabled ({face_type_str}, style {face_style_str}, strength {face_strength}, top {self.spin_face_blur_pct.value()}% of face)" if self.chk_face_blur.isChecked() else "Disabled"
        bblur_status = f"Enabled (kernel {self.spin_bg_strength.value()}px)" if self.chk_bg_blur.isChecked() else "Disabled"
        
        details = f"""
Input: {os.path.basename(self.selected_video_path)}
Output: {os.path.basename(output_path)}
Resolution: {video_w}x{video_h}

- CUDA Hardware Acceleration: {cuda_status}
- Face Blur (Face detector): {fblur_status}
- Background Blur (Selfie segmenter): {bblur_status}
- Interactive text overlays: {len(texts_to_backend)} text(s) definition mapped
"""
        msg_box.setInformativeText(details)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        res = msg_box.exec()
        if res == QMessageBox.StandardButton.No:
            self.log_message.emit("Export canceled by user.")
            return
            
        self.btn_start_process.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText("Processing starting...")
        self.log_message.emit("Starting AI processing thread...")
        
        self.worker = AIProcessWorker(
            input_path=self.selected_video_path,
            output_path=output_path,
            texts=texts_to_backend,
            use_cuda=self.chk_cuda.isChecked(),
            face_blur=self.chk_face_blur.isChecked(),
            face_blur_pct=float(self.spin_face_blur_pct.value()),
            face_blur_type=self.cb_face_blur_type.currentData(),
            face_blur_image_path=self.txt_face_image_path.text() if self.cb_face_blur_type.currentData() == "Image" else None,
            face_blur_style=self.cb_face_blur_style.currentData(),
            face_blur_strength=self.spin_face_blur_strength.value(),
            bg_blur=self.chk_bg_blur.isChecked(),
            bg_blur_strength=self.spin_bg_strength.value()
        )
        
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_progress(self, percent, text):
        self.progress_bar.setValue(percent)
        self.lbl_progress_status.setText(text)

    def on_worker_finished(self, success, msg):
        self.btn_start_process.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            self.lbl_progress_status.setText("Finished Successfully!")
            self.log_message.emit("AI Processing thread completed successfully.")
            QMessageBox.information(self, "Success", "Video processed and exported successfully!")
        else:
            self.progress_bar.setValue(0)
            self.lbl_progress_status.setText("Error during process!")
            self.log_message.emit(f"AI Process Error: {msg}")
            QMessageBox.critical(self, "Error", f"An error occurred during video processing:\n{msg}")