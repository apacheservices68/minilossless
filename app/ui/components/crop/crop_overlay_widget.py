
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt6.QtGui import QBrush, QPainter, QColor, QPen, QPainterPath, QRegion

class CropOverlayWidget(QWidget):
    crop_rect_changed = pyqtSignal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.crop_rect = QRect() # This rect is in video coordinates
        self.video_width = 1
        self.video_height = 1
        self.is_drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_video_resolution(self, width, height):
        self.video_width = width if width > 0 else 1
        self.video_height = height if height > 0 else 1
        self.update()

    def get_display_crop_rect(self) -> QRect:
        scale_x = self.width() / float(self.video_width) if self.video_width > 0 else 1.0
        scale_y = self.height() / float(self.video_height) if self.video_height > 0 else 1.0

        display_x = int(self.crop_rect.x() * scale_x)
        display_y = int(self.crop_rect.y() * scale_y)
        display_w = int(self.crop_rect.width() * scale_x)
        display_h = int(self.crop_rect.height() * scale_y)
        return QRect(display_x, display_y, display_w, display_h)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        display_rect = self.get_display_crop_rect()

        # 1. MỜ VÙNG XUNG QUANH BẰNG QRegion (Đục lỗ vùng Crop)
        full_region = QRegion(self.rect())
        if display_rect.isValid() and not display_rect.isEmpty():
            crop_region = QRegion(display_rect)
            dim_region = full_region.subtracted(crop_region)
        else:
            dim_region = full_region

        painter.setClipRegion(dim_region)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 140))
        painter.setClipping(False)

        # 2. VẼ KHUNG VIỀN VÀNG NỔI BẬT
        if display_rect.isValid() and not display_rect.isEmpty():
            pen = QPen(QColor("yellow"), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(display_rect)

            # 3. VẼ 8 TAY CẦM CO GIÃN (RESIZE HANDLES)
            handles = self.get_handle_points(display_rect)
            painter.setPen(QPen(QColor("black"), 1))
            painter.setBrush(QBrush(QColor("yellow")))
            for h in handles:
                painter.drawRect(h.x() - 4, h.y() - 4, 8, 8)
                
    def get_handle_points(self, r: QRect):
        return [
            r.topLeft(), r.topRight(), r.bottomLeft(), r.bottomRight(),
            QPoint(r.left() + r.width() // 2, r.top()),
            QPoint(r.left() + r.width() // 2, r.bottom()),
            QPoint(r.left(), r.top() + r.height() // 2),
            QPoint(r.right(), r.top() + r.height() // 2),
        ]

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update() # Trigger repaint

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_point = event.pos()
            widget_rect = QRect(self.start_point, self.end_point).normalized()

            scale_x = float(self.video_width) / self.width() if self.width() > 0 else 1.0
            scale_y = float(self.video_height) / self.height() if self.height() > 0 else 1.0

            video_x = int(widget_rect.x() * scale_x)
            video_y = int(widget_rect.y() * scale_y)
            video_w = int(widget_rect.width() * scale_x)
            video_h = int(widget_rect.height() * scale_y)

            self.crop_rect = QRect(video_x, video_y, video_w, video_h)
            self.crop_rect_changed.emit(self.crop_rect)
            self.update() # Trigger repaint

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            # Finalize crop rect
            self.mouseMoveEvent(event)

    def set_crop_rect(self, rect):
        if self.crop_rect != rect:
            self.crop_rect = rect
            self.update()

    def reset_ui(self):
        self.set_video_resolution(0, 0)
        self.set_crop_rect(QRect(0, 0, 0, 0))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()
