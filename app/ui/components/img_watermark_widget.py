# Added on 08132026: [VI] Import cac thu vien can thiet / [EN] Import necessary libraries
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QCheckBox, QLineEdit, QPushButton, QFileDialog, QLabel
)

# Added on 08132026: [VI] Dinh nghia widget cho watermark hinh anh / [EN] Define the image watermark widget
class ImgWatermarkWidget(QWidget):
    # Added on 08132026: [VI] Khoi tao widget / [EN] Initialize the widget
    def __init__(self, parent=None):
        # Added on 08132026: [VI] Goi ham khoi tao cua lop cha / [EN] Call parent constructor
        super().__init__(parent)
        # Added on 08132026: [VI] Khoi tao giao dien / [EN] Initialize the UI
        self.init_ui()

    # Added on 08132026: [VI] Khoi tao giao dien / [EN] Initialize the UI
    def init_ui(self):
        # Added on 08132026: [VI] Tao layout chinh / [EN] Create the main layout
        layout = QVBoxLayout(self)
        # Added on 08132026: [VI] Xoa bo khoang trong thua / [EN] Remove margins
        layout.setContentsMargins(0, 5, 0, 0)

        # Added on 08132026: [VI] Tao checkbox de bat/tat watermark hinh anh / [EN] Create checkbox to enable/disable image watermark
        self.chk_use_image = QCheckBox("Use Image Watermark")
        # Added on 08132026: [VI] Ket noi su kien toggled / [EN] Connect the toggled signal
        self.chk_use_image.toggled.connect(self.on_toggle_image_watermark)
        # Added on 08132026: [VI] Them vao layout / [EN] Add to layout
        layout.addWidget(self.chk_use_image)

        # Added on 08132026: [VI] Tao widget chua trinh chon file / [EN] Create a container widget for the file picker
        self.file_picker_widget = QWidget()
        # Added on 08132026: [VI] Tao layout cho trinh chon file / [EN] Create layout for the file picker
        file_picker_layout = QHBoxLayout(self.file_picker_widget)
        # Added on 08132026: [VI] Xoa bo khoang trong thua / [EN] Remove margins
        file_picker_layout.setContentsMargins(0, 0, 0, 0)

        # Added on 08132026: [VI] Tao o nhap duong dan file / [EN] Create line edit for the file path
        self.txt_image_path = QLineEdit()
        # Added on 08132026: [VI] Chi cho phep doc / [EN] Set as read-only
        self.txt_image_path.setReadOnly(True)
        # Added on 08132026: [VI] Them vao layout / [EN] Add to layout
        file_picker_layout.addWidget(self.txt_image_path)

        # Added on 08132026: [VI] Tao nut "Browse..." / [EN] Create "Browse..." button
        btn_browse = QPushButton("Browse...")
        # Added on 08132026: [VI] Ket noi su kien click / [EN] Connect click signal
        btn_browse.clicked.connect(self.browse_image)
        # Added on 08132026: [VI] Them vao layout / [EN] Add to layout
        file_picker_layout.addWidget(btn_browse)

        # Added on 08132026: [VI] Them widget chon file vao layout chinh / [EN] Add file picker widget to the main layout
        layout.addWidget(self.file_picker_widget)

        # Added on 08132026: [VI] An widget chon file ban dau / [EN] Hide the file picker widget initially
        self.file_picker_widget.setVisible(False)

    # Added on 08132026: [VI] Xu ly su kien toggled cua checkbox / [EN] Handle the checkbox toggle event
    def on_toggle_image_watermark(self, checked):
        # Added on 08132026: [VI] An/Hien widget chon file / [EN] Show/Hide the file picker widget
        self.file_picker_widget.setVisible(checked)
        # Added on 08132026: [VI] Neu bo check, xoa duong dan / [EN] If unchecked, clear the path
        if not checked:
            # Added on 08132026: [VI] Xoa text / [EN] Clear text
            self.txt_image_path.clear()

    # Added on 08132026: [VI] Xu ly su kien click nut "Browse..." / [EN] Handle the "Browse..." button click event
    def browse_image(self):
        # Added on 08132026: [VI] Mo hop thoai chon file / [EN] Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Watermark Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        # Added on 08132026: [VI] Neu co chon file / [EN] If a file was selected
        if file_path:
            # Added on 08132026: [VI] Hien thi duong dan / [EN] Set the file path
            self.txt_image_path.setText(file_path)
