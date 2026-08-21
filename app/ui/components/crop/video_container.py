
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QSize, Qt

class VideoContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_widget = None
        self.aspect_ratio = 16 / 9.0

    def set_video_widget(self, widget):
        self.video_widget = widget
        self.video_widget.setParent(self)

    def set_aspect_ratio(self, ratio):
        self.aspect_ratio = ratio
        self.resizeEvent(None) # Trigger a resize

    def resizeEvent(self, event):
        if self.video_widget:
            size = self.size()
            new_size = QSize(size.width(), int(size.width() / self.aspect_ratio))
            if new_size.height() > size.height():
                new_size = QSize(int(size.height() * self.aspect_ratio), size.height())
            
            # Center the video widget
            x = (size.width() - new_size.width()) / 2
            y = (size.height() - new_size.height()) / 2
            self.video_widget.setGeometry(int(x), int(y), new_size.width(), new_size.height())

        super().resizeEvent(event)
