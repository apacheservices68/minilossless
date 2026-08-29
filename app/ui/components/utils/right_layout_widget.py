from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from .right_rotate_block_widget import RightRotateBlockWidget
from .right_resize_block_widget import RightResizeBlockWidget
from PyQt6.QtCore import Qt

class RightLayoutWidget(QWidget):
    """
    A widget that arranges the rotate and resize control blocks vertically.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface by arranging child widgets.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.setSpacing(15)

        self.rotate_block = RightRotateBlockWidget()
        self.resize_block = RightResizeBlockWidget()

        main_layout.addWidget(self.rotate_block)
        main_layout.addWidget(self.resize_block)
        self.lbl_progress_status = QLabel("Idle")
        self.lbl_progress_status.setText("Idle")
        self.lbl_progress_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_progress_status)
        main_layout.addStretch()

        self.setLayout(main_layout)
        self.setFixedWidth(350)

    def reset_ui(self):
        """
        Resets the UI of all child control blocks.
        """
        self.rotate_block.reset_ui()
        self.resize_block.reset_ui()
        self.lbl_progress_status.setText("Idle")
