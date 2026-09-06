from PyQt6.QtWidgets import (
    QGroupBox, QGridLayout, QLabel, QSpinBox, QCheckBox, QPushButton
)
from PyQt6.QtCore import Qt

class RightResizeBlockWidget(QGroupBox):
    """
    Widget block for video resizing controls.
    """
    def __init__(self, parent=None):
        super().__init__("Resize Video", parent)
        self.original_width = 0
        self.original_height = 0
        self.aspect_ratio = 1.0
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """
        Initializes the user interface for the resize block.
        """
        layout = QGridLayout(self)

        layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(0, 9999)
        layout.addWidget(self.width_spinbox, 0, 1)

        layout.addWidget(QLabel("Height:"), 1, 0)
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(0, 9999)
        layout.addWidget(self.height_spinbox, 1, 1)

        self.keep_aspect_ratio_checkbox = QCheckBox("Keep Aspect Ratio")
        self.keep_aspect_ratio_checkbox.setChecked(True)
        layout.addWidget(self.keep_aspect_ratio_checkbox, 2, 0, 1, 2)

        self.apply_button = QPushButton("Apply Resize")
        layout.addWidget(self.apply_button, 3, 0, 1, 2)

        self.setLayout(layout)

    def connect_signals(self):
        """
        Connects widget signals to appropriate slots.
        """
        self.width_spinbox.valueChanged.connect(self.on_width_changed)
        self.height_spinbox.valueChanged.connect(self.on_height_changed)

    def set_original_dimensions(self, width, height):
        """
        Sets the original video dimensions and calculates the aspect ratio.
        """
        self.original_width = width
        self.original_height = height
        if self.original_height > 0:
            self.aspect_ratio = self.original_width / self.original_height
        else:
            self.aspect_ratio = 1.0
        
        self.width_spinbox.blockSignals(True)
        self.height_spinbox.blockSignals(True)
        self.width_spinbox.setValue(self.original_width)
        self.height_spinbox.setValue(self.original_height)
        self.width_spinbox.blockSignals(False)
        self.height_spinbox.blockSignals(False)


    def on_width_changed(self, width):
        """
        Adjusts height based on width if 'Keep Aspect Ratio' is checked.
        """
        if self.keep_aspect_ratio_checkbox.isChecked():
            self.height_spinbox.blockSignals(True)
            new_height = int(width / self.aspect_ratio)
            self.height_spinbox.setValue(new_height)
            self.height_spinbox.blockSignals(False)

    def on_height_changed(self, height):
        """
        Adjusts width based on height if 'Keep Aspect Ratio' is checked.
        """
        if self.keep_aspect_ratio_checkbox.isChecked():
            self.width_spinbox.blockSignals(True)
            new_width = int(height * self.aspect_ratio)
            self.width_spinbox.setValue(new_width)
            self.width_spinbox.blockSignals(False)

    def get_values(self):
        """
        Returns the current width and height values.

        Returns:
            tuple: A tuple containing (width, height).
        """
        return self.width_spinbox.value(), self.height_spinbox.value()

    def reset_ui(self):
        """
        Resets the UI elements to their default state.
        """
        self.original_width = 0
        self.original_height = 0
        self.aspect_ratio = 1.0
        
        self.width_spinbox.blockSignals(True)
        self.height_spinbox.blockSignals(True)
        self.width_spinbox.setValue(0)
        self.height_spinbox.setValue(0)
        self.width_spinbox.blockSignals(False)
        self.height_spinbox.blockSignals(False)
        self.keep_aspect_ratio_checkbox.setChecked(True)
