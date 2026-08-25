from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt

class ExportPipelineWidget(QWidget):
    start_export = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        process_group = QGroupBox("Export & Process Pipeline")
        process_layout = QVBoxLayout()
        
        self.btn_start_process = QPushButton("🚀 Run AI Export Pipeline (Re-encode)")
        self.btn_start_process.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px; padding: 10px;")
        self.btn_start_process.clicked.connect(self.start_export.emit)
        process_layout.addWidget(self.btn_start_process)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Progress: %p%")
        process_layout.addWidget(self.progress_bar)
        
        self.lbl_progress_status = QLabel("Idle")
        self.lbl_progress_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        process_layout.addWidget(self.lbl_progress_status)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)

    def set_progress(self, percent, text):
        self.progress_bar.setValue(percent)
        self.lbl_progress_status.setText(text)

    def reset(self):
        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText("Idle")
        self.btn_start_process.setEnabled(True)
        self.btn_start_process.setText("🚀 Run AI Export Pipeline (Re-encode)")

    def set_processing_state(self, is_processing):
        self.btn_start_process.setEnabled(not is_processing)
        if is_processing:
            self.btn_start_process.setText("⏳ Processing AI Video...")
            self.lbl_progress_status.setText("Processing starting...")
        else:
            self.btn_start_process.setText("🚀 Run AI Export Pipeline (Re-encode)")
        
