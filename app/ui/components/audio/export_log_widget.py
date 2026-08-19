
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QProgressBar, QTextEdit
)

class ExportLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()

        # Export Button
        self.export_button = QPushButton("Export Process")
        export_layout.addWidget(self.export_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        export_layout.addWidget(self.progress_bar)

        # Console Log
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        export_layout.addWidget(self.console_log)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
