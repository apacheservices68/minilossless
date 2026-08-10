# app/ui/components/snapshot_widget.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox, QLineEdit

class SnapshotWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        self.btn_snapshot = QPushButton("📸 Capture")
        self.cb_snapshot_format = QComboBox()
        self.cb_snapshot_format.addItem("JPG", "jpg")
        self.cb_snapshot_format.addItem("PNG", "png")
        self.txt_snapshot_pattern = QLineEdit("[filename]_Frame_[timestamp].[ext]")

        layout.addWidget(self.btn_snapshot)
        layout.addWidget(self.cb_snapshot_format)
        layout.addWidget(self.txt_snapshot_pattern, 1)
