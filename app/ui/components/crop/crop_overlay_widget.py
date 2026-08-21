
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

class CropOverlayWidget(QWidget):
    crop_rect_changed = pyqtSignal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.crop_rect = QRect()
        self.is_drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)


    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimming effect
        dim_color = QColor(0, 0, 0, 150)
        painter.fillRect(self.rect(), dim_color)

        if not self.crop_rect.isNull():
            # Clear the crop area
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.crop_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Draw crop rectangle border
            pen = QPen(QColor("#FFFFFF"), 1, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.crop_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_point = event.pos()
            self.crop_rect = QRect(self.start_point, self.end_point).normalized()
            self.crop_rect_changed.emit(self.crop_rect)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.crop_rect = QRect(self.start_point, self.end_point).normalized()
            self.crop_rect_changed.emit(self.crop_rect)
            self.update()

    def set_crop_rect(self, rect):
        if self.crop_rect != rect:
            self.crop_rect = rect
            self.update()
