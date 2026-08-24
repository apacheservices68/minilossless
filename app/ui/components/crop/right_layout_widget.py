from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QSpinBox, QPushButton
)
from PyQt6.QtCore import Qt


class RightLayoutWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 0, 10, 10)

        # Controls Group
        self.controls_group = QGroupBox("Controls")
        self.controls_layout = QGridLayout(self.controls_group)

        # Position
        self.pos_group = QGroupBox("Position")
        self.pos_layout = QGridLayout()
        self.pos_layout.addWidget(QLabel("Pos X:"), 0, 0)
        self.pos_x_spinbox = QSpinBox()
        self.pos_layout.addWidget(self.pos_x_spinbox, 0, 1)
        self.pos_layout.addWidget(QLabel("Pos Y:"), 1, 0)
        self.pos_y_spinbox = QSpinBox()
        self.pos_layout.addWidget(self.pos_y_spinbox, 1, 1)
        self.pos_group.setLayout(self.pos_layout)

        # Size
        size_group = QGroupBox("Size")
        self.size_layout = QGridLayout()
        self.size_layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_spinbox = QSpinBox()
        self.size_layout.addWidget(self.width_spinbox, 0, 1)
        self.size_layout.addWidget(QLabel("Height:"), 1, 0)
        self.height_spinbox = QSpinBox()
        self.size_layout.addWidget(self.height_spinbox, 1, 1)
        size_group.setLayout(self.size_layout)

        self.controls_layout.addWidget(self.pos_group, 0, 0)
        self.controls_layout.addWidget(size_group, 1, 0)
        self.controls_group.setLayout(self.controls_layout)

        # Process Output Group
        self.process_group = QGroupBox("Process Output")
        self.process_layout = QVBoxLayout()
        self.process_button = QPushButton("Process Crop Video")
        self.process_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.process_layout.addWidget(self.process_button)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.process_layout.addWidget(self.reset_button)
        self.process_group.setLayout(self.process_layout)

        self.main_layout.addWidget(self.controls_group)
        self.main_layout.addWidget(self.process_group)
        self.main_layout.addStretch()

        self.setFixedWidth(350)

        # main_container = QWidget()
        # main_container.setLayout(self.main_layout)
        # main_container.setFixedWidth(350)
        # return main_container

    def reset_ui(self):
        self.pos_x_spinbox.setValue(0)
        self.pos_y_spinbox.setValue(0)
        self.width_spinbox.setValue(0)
        self.height_spinbox.setValue(0)
        self.process_button.setEnabled(True)
        self.process_button.setText("Process Crop Video")