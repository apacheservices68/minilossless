import os
from PyQt6.QtWidgets import QWidget, QGroupBox, QHBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt6.QtCore import pyqtSignal

class VideoSourceWidget(QWidget):
    # Signal phát ra đường dẫn file video khi người dùng chọn xong file
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = ""
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        file_group = QGroupBox("Video Input Source")
        file_layout = QHBoxLayout()

        self.lbl_video_path = QLabel("No video selected. Click 'Open Video' to select one.")
        self.lbl_video_path.setWordWrap(True)

        self.btn_open = QPushButton("Open Video")
        self.btn_open.setObjectName("btn_open")
        self.btn_open.clicked.connect(self.open_video_dialog)

        file_layout.addWidget(self.lbl_video_path, 1)
        file_layout.addWidget(self.btn_open)
        file_group.setLayout(file_layout)

        main_layout.addWidget(file_group)

    def open_video_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.flv);;All Files (*)"
        )
        if file_path:
            self.file_selected.emit(file_path)

    def set_video_path(self, path: str):
        """Cập nhật giao diện hiển thị đường dẫn video"""
        self.selected_file = path
        if path:
            filename = os.path.basename(path)
            self.lbl_video_path.setText(f"Selected: {filename}\nFull Path: {path}")
        else:
            self.lbl_video_path.setText("No video selected. Click 'Open Video' to select one.")

    def get_video_path(self) -> str:
        """Lấy đường dẫn video hiện tại"""
        return self.selected_file