from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QComboBox, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal

class RightRotateBlockWidget(QGroupBox):
    """
    Widget block for Rotate & Flip controls.
    """
    preview_rotate_requested = pyqtSignal(str)
    apply_rotate_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Rotate & Flip", parent)
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """
        Initializes the user interface for the rotate and flip block.
        """
        layout = QVBoxLayout(self)

        self.rotate_options_dropdown = QComboBox()
        self.rotate_options_dropdown.addItems([
            "None", "Rotate 90°", "Rotate 180°", "Rotate 270°", "Horizontal Flip", "Vertical Flip"
        ])
        layout.addWidget(self.rotate_options_dropdown)

        buttons_layout = QHBoxLayout()
        self.preview_button = QPushButton("Preview Rotate")
        self.apply_button = QPushButton("Apply Rotate")
        buttons_layout.addWidget(self.preview_button)
        buttons_layout.addWidget(self.apply_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def connect_signals(self):
        """
        Connects widget signals to appropriate slots.
        """
        self.preview_button.clicked.connect(self.on_preview)
        self.apply_button.clicked.connect(self.on_apply)

    def on_preview(self):
        """
        Emits a signal with the selected rotation/flip option for preview.
        """
        self.preview_rotate_requested.emit(self.get_values())

    def on_apply(self):
        """
        Emits a signal with the selected rotation/flip option to be applied.
        """
        self.apply_rotate_requested.emit(self.get_values())

    def get_values(self):
        """
        Returns the currently selected rotation or flip option.

        Returns:
            str: The selected option text.
        """
        return self.rotate_options_dropdown.currentText()

    def reset_ui(self):
        """
        Resets the UI elements to their default state.
        """
        self.rotate_options_dropdown.setCurrentIndex(0)
