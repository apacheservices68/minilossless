
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QFont

class RulerWidget(QWidget):
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.max_value = 1920  # Default max value
        if self.orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(30)
        else:
            self.setFixedWidth(30)

    def set_max_value(self, value):
        self.max_value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Arial", 8)
        painter.setFont(font)
        pen = QPen(Qt.GlobalColor.white)
        painter.setPen(pen)

        if self.orientation == Qt.Orientation.Horizontal:
            self.draw_horizontal_ruler(painter)
        else:
            self.draw_vertical_ruler(painter)

    def draw_horizontal_ruler(self, painter):
        width = self.width()
        step = 100
        for i in range(0, self.max_value, step):
            x = int((i / self.max_value) * width)
            painter.drawLine(x, self.height() - 5, x, self.height())
            painter.drawText(x + 2, self.height() - 7, str(i))
        for i in range(0, self.max_value, step // 2):
            x = int((i / self.max_value) * width)
            painter.drawLine(x, self.height() - 3, x, self.height())

    def draw_vertical_ruler(self, painter):
        height = self.height()
        step = 100
        for i in range(0, self.max_value, step):
            y = int((i / self.max_value) * height)
            painter.drawLine(self.width() - 5, y, self.width(), y)
            painter.save()
            painter.translate(self.width() - 15, y + 2)
            painter.rotate(90)
            painter.drawText(0, 0, str(i))
            painter.restore()
        for i in range(0, self.max_value, step // 2):
            y = int((i / self.max_value) * height)
            painter.drawLine(self.width() - 3, y, self.width(), y)
