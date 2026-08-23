from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QFont

class RulerWidget(QWidget):
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.max_value = 1920
        if self.orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(30)
        else:
            self.setFixedWidth(30)

    def set_max_value(self, value):
        self.max_value = value if value > 0 else 1920
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
        
        if self.max_value > 1500:
            step = 200
        elif self.max_value > 800:
            step = 100
        else:
            step = 50

        for i in range(0, self.max_value + 1, step):
            x = int((i / self.max_value) * width)
            painter.drawLine(x, self.height() - 5, x, self.height())
            
            # Căn Y đúng chuẩn self.height() - 7 cho tất cả các số
            if x > width - 35:
                painter.drawText(x - 10, self.height() - 7, str(i))
            else:
                painter.drawText(x + 2, self.height() - 7, str(i))

        # Vạch phụ (Sub-ticks)
        sub_step = step // 2
        for i in range(0, self.max_value + 1, sub_step):
            x = int((i / self.max_value) * width)
            painter.drawLine(x, self.height() - 3, x, self.height())

    def draw_vertical_ruler(self, painter):
        height = self.height()
        
        if self.max_value > 1500:
            step = 200
        elif self.max_value > 800:
            step = 100
        else:
            step = 50

        for i in range(0, self.max_value + 1, step):
            y = int((i / self.max_value) * height)
            painter.drawLine(self.width() - 5, y, self.width(), y)
            
            painter.save()
            if y > height - 25:
                painter.translate(self.width() - 15, y - 12)
            else:
                painter.translate(self.width() - 15, y + 2)
                
            painter.rotate(90)
            painter.drawText(0, 0, str(i))
            painter.restore()

        sub_step = step // 2
        for i in range(0, self.max_value + 1, sub_step):
            y = int((i / self.max_value) * height)
            painter.drawLine(self.width() - 3, y, self.width(), y)