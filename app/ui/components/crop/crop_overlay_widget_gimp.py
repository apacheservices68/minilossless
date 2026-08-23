
"""
This is the implementation of the GIMP-style crop overlay widget.

It is designed to be a container for the video widget, allowing it to draw the crop
overlay directly on top of the video content. This approach solves the rendering
issues on Linux where native video surfaces (X11/VAAPI) would otherwise obscure
any overlapping widgets.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QBrush, QCursor

class CropOverlayWidgetGIMP(QWidget):
    crop_rect_changed = pyqtSignal(QRect)

    # Enum for handle positions
    TopLeft, Top, TopRight, Right, BottomRight, Bottom, BottomLeft, Left, Move = range(9)

    def __init__(self, video_widget, parent=None):
        super().__init__(parent)
        self.video_widget = video_widget
        self.crop_rect = QRect()  # In video coordinates
        self.video_width = 1
        self.video_height = 1

        self.is_dragging = False
        self.drag_handle = None
        self.drag_start_pos = QPoint()
        self.drag_start_rect = QRect()

        self.handle_size = 8
        self.handles = {}
        self.handle_cursors = {
            self.TopLeft: Qt.CursorShape.SizeFDiagCursor,
            self.TopRight: Qt.CursorShape.SizeBDiagCursor,
            self.BottomLeft: Qt.CursorShape.SizeBDiagCursor,
            self.BottomRight: Qt.CursorShape.SizeFDiagCursor,
            self.Top: Qt.CursorShape.SizeVerCursor,
            self.Bottom: Qt.CursorShape.SizeVerCursor,
            self.Left: Qt.CursorShape.SizeHorCursor,
            self.Right: Qt.CursorShape.SizeHorCursor,
            self.Move: Qt.CursorShape.SizeAllCursor
        }

        self.init_ui()

    def init_ui(self):
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        # Bắt buộc: video_widget là con của overlay này để vẽ đè lên
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_widget)
        self.setLayout(layout)
        
        # Set size policy to expand
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


    def set_video_resolution(self, width, height):
        self.video_width = width if width > 0 else 1
        self.video_height = height if height > 0 else 1
        self.update()

    def set_crop_rect(self, rect: QRect):
        if self.crop_rect != rect:
            self.crop_rect = rect
            self.crop_rect_changed.emit(self.crop_rect)
            self.update() # Schedule a repaint

    def get_display_rect(self) -> QRect:
        '''Converts video-coordinate crop_rect to widget-coordinate display_rect.'''
        if not self.video_widget or self.video_width == 1 or self.video_height == 1:
            return QRect()

        video_widget_rect = self.video_widget.geometry()
        
        scale_x = video_widget_rect.width() / self.video_width
        scale_y = video_widget_rect.height() / self.video_height

        return QRect(
            int(self.crop_rect.x() * scale_x) + video_widget_rect.x(),
            int(self.crop_rect.y() * scale_y) + video_widget_rect.y(),
            int(self.crop_rect.width() * scale_x),
            int(self.crop_rect.height() * scale_y)
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        display_rect = self.get_display_rect()
        if not display_rect.isValid():
            return

        # 1. Darkened Mask around the crop area
        path = QPainterPath()
        path.addRect(QRectF(self.rect()))
        path.addRect(QRectF(display_rect))
        path.setFillRule(Qt.FillRule.OddEvenFill)
        painter.fillPath(path, QColor(0, 0, 0, 150))

        # 2. GIMP Style Crop Frame
        # 1px Black border
        pen = QPen(Qt.GlobalColor.black, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(display_rect).adjusted(0.5, 0.5, -0.5, -0.5))

        # Rule of Thirds Grid
        pen.setColor(QColor(255, 255, 255, 150))
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)

        one_third_w = display_rect.width() / 3
        one_third_h = display_rect.height() / 3
        painter.drawLine(QPointF(display_rect.left() + one_third_w, display_rect.top()), QPointF(display_rect.left() + one_third_w, display_rect.bottom()))
        painter.drawLine(QPointF(display_rect.left() + 2 * one_third_w, display_rect.top()), QPointF(display_rect.left() + 2 * one_third_w, display_rect.bottom()))
        painter.drawLine(QPointF(display_rect.left(), display_rect.top() + one_third_h), QPointF(display_rect.right(), display_rect.top() + one_third_h))
        painter.drawLine(QPointF(display_rect.left(), display_rect.top() + 2 * one_third_h), QPointF(display_rect.right(), display_rect.top() + 2 * one_third_h))

        # 3. Resize Handles
        self.update_handle_rects(display_rect)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        for handle in self.handles.values():
            painter.drawRect(handle)

    def update_handle_rects(self, r: QRect):
        hs = self.handle_size
        hs2 = hs // 2
        self.handles = {
            self.TopLeft: QRect(r.topLeft().x() - hs2, r.topLeft().y() - hs2, hs, hs),
            self.TopRight: QRect(r.topRight().x() - hs2, r.topRight().y() - hs2, hs, hs),
            self.BottomLeft: QRect(r.bottomLeft().x() - hs2, r.bottomLeft().y() - hs2, hs, hs),
            self.BottomRight: QRect(r.bottomRight().x() - hs2, r.bottomRight().y() - hs2, hs, hs),
            self.Top: QRect(r.center().x() - hs2, r.top() - hs2, hs, hs),
            self.Bottom: QRect(r.center().x() - hs2, r.bottom() - hs2, hs, hs),
            self.Left: QRect(r.left() - hs2, r.center().y() - hs2, hs, hs),
            self.Right: QRect(r.right() - hs2, r.center().y() - hs2, hs, hs),
        }

    def get_handle_at_pos(self, pos: QPoint):
        for handle, rect in self.handles.items():
            if rect.contains(pos):
                return handle
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_handle = self.get_handle_at_pos(event.pos())
            if self.drag_handle is not None:
                self.is_dragging = True
                self.drag_start_pos = event.pos()
                self.drag_start_rect = QRect(self.crop_rect) # Work on a copy
            elif self.get_display_rect().contains(event.pos()):
                self.is_dragging = True
                self.drag_handle = self.Move
                self.drag_start_pos = event.pos()
                self.drag_start_rect = QRect(self.crop_rect)

    def mouseMoveEvent(self, event):
        if not self.is_dragging:
            handle = self.get_handle_at_pos(event.pos())
            if handle is not None:
                self.setCursor(self.handle_cursors[handle])
            elif self.get_display_rect().contains(event.pos()):
                self.setCursor(self.handle_cursors[self.Move])
            else:
                self.unsetCursor()
        else:
            self.process_drag(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.drag_handle = None
            self.unsetCursor()

    def process_drag(self, current_pos: QPoint):
        if not self.is_dragging or not self.video_widget:
            return

        video_widget_rect = self.video_widget.geometry()
        scale_x = self.video_width / video_widget_rect.width()
        scale_y = self.video_height / video_widget_rect.height()
        
        delta = current_pos - self.drag_start_pos
        dx = delta.x() * scale_x
        dy = delta.y() * scale_y

        new_rect = QRect(self.drag_start_rect)

        if self.drag_handle == self.Move:
            new_rect.translate(int(dx), int(dy))
        elif self.drag_handle == self.TopLeft:
            new_rect.setTopLeft(self.drag_start_rect.topLeft() + QPoint(int(dx), int(dy)))
        elif self.drag_handle == self.TopRight:
            new_rect.setTopRight(self.drag_start_rect.topRight() + QPoint(int(dx), int(dy)))
        # ... (and so on for all handles)
        elif self.drag_handle == self.Top:
            new_rect.setTop(self.drag_start_rect.top() + int(dy))
        elif self.drag_handle == self.Bottom:
            new_rect.setBottom(self.drag_start_rect.bottom() + int(dy))
        elif self.drag_handle == self.Left:
            new_rect.setLeft(self.drag_start_rect.left() + int(dx))
        elif self.drag_handle == self.Right:
            new_rect.setRight(self.drag_start_rect.right() + int(dx))
        elif self.drag_handle == self.BottomLeft:
            new_rect.setBottomLeft(self.drag_start_rect.bottomLeft() + QPoint(int(dx), int(dy)))
        elif self.drag_handle == self.BottomRight:
            new_rect.setBottomRight(self.drag_start_rect.bottomRight() + QPoint(int(dx), int(dy)))

        # Normalize the rectangle to ensure width/height are positive
        final_rect = new_rect.normalized()
        
        # Constrain rect to video boundaries
        final_rect.setX(max(0, final_rect.x()))
        final_rect.setY(max(0, final_rect.y()))
        final_rect.setRight(min(self.video_width, final_rect.right()))
        final_rect.setBottom(min(self.video_height, final_rect.bottom()))

        if self.crop_rect != final_rect:
            self.set_crop_rect(final_rect)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()

