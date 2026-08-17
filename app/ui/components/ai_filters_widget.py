from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QCheckBox, QSpinBox, QComboBox, QGroupBox, QFormLayout, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

class AIFiltersWidget(QWidget):
    state_changed = pyqtSignal()
    cuda_state_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        ai_group = QGroupBox("AI Filters & Hardware Acceleration")
        ai_layout = QFormLayout()
        
        self.chk_cuda = QCheckBox("Enable CUDA Hardware Acceleration")
        
        self.chk_face_blur = QCheckBox("Face Blur (Blur mặt)")
        self.spin_face_blur_pct = QSpinBox()
        self.spin_face_blur_pct.setRange(0, 100)
        self.spin_face_blur_pct.setValue(0)
        self.spin_face_blur_pct.setSuffix(" % top portion")
        
        self.cb_face_blur_type = QComboBox()
        self.cb_face_blur_type.addItem("Square (Hình vuông)", "Square")
        self.cb_face_blur_type.addItem("Circle/Ellipse (Hình elip)", "Ellipse")
        self.cb_face_blur_type.addItem("Replace with Image (Thay thế bằng ảnh)", "Image")
        self.cb_face_blur_type.currentIndexChanged.connect(self.on_face_blur_type_changed)
        
        self.cb_face_blur_style = QComboBox()
        self.cb_face_blur_style.addItem("Gaussian (Làm mờ mịn)", "Gaussian")
        self.cb_face_blur_style.addItem("Pixelate (Mô-sắc/Pixel)", "Pixel")
        self.cb_face_blur_style.addItem("Box Blur (Làm mờ hộp)", "Box")
        self.cb_face_blur_style.addItem("Blackout (Màu đặc)", "Blackout")
        
        self.spin_face_blur_strength = QSpinBox()
        self.spin_face_blur_strength.setRange(1, 100)
        self.spin_face_blur_strength.setValue(15)
        
        self.widget_face_image = QWidget()
        face_img_layout = QHBoxLayout(self.widget_face_image)
        face_img_layout.setContentsMargins(0, 0, 0, 0)
        self.txt_face_image_path = QLineEdit()
        self.txt_face_image_path.setPlaceholderText("Select replacement image...")
        self.btn_face_image_browse = QPushButton("Browse...")
        self.btn_face_image_browse.clicked.connect(self.browse_face_replacement_image)
        face_img_layout.addWidget(self.txt_face_image_path, 1)
        face_img_layout.addWidget(self.btn_face_image_browse)
        self.widget_face_image.setVisible(False)
        
        self.chk_bg_blur = QCheckBox("Background Blur (Xóa phông)")
        self.spin_bg_strength = QSpinBox()
        self.spin_bg_strength.setRange(1, 499)
        self.spin_bg_strength.setSingleStep(2)
        self.spin_bg_strength.setValue(101)
        self.spin_bg_strength.setSuffix(" px kernel")
        
        ai_layout.addRow(self.chk_cuda)
        ai_layout.addRow(self.chk_face_blur, self.spin_face_blur_pct)
        ai_layout.addRow("Shape/Replace Type:", self.cb_face_blur_type)
        ai_layout.addRow("Blur Style:", self.cb_face_blur_style)
        ai_layout.addRow("Blur Strength / Pixel Size:", self.spin_face_blur_strength)
        ai_layout.addRow("Replacement Image:", self.widget_face_image)
        ai_layout.addRow(self.chk_bg_blur, self.spin_bg_strength)
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        self.chk_cuda.stateChanged.connect(lambda state: self.cuda_state_changed.emit(state == Qt.CheckState.Checked.value))
        self.chk_cuda.stateChanged.connect(self.state_changed.emit)
        self.chk_face_blur.stateChanged.connect(self.state_changed.emit)
        self.spin_face_blur_pct.valueChanged.connect(self.state_changed.emit)
        self.cb_face_blur_type.currentIndexChanged.connect(self.state_changed.emit)
        self.cb_face_blur_style.currentIndexChanged.connect(self.state_changed.emit)
        self.spin_face_blur_strength.valueChanged.connect(self.state_changed.emit)
        self.chk_bg_blur.stateChanged.connect(self.state_changed.emit)
        self.spin_bg_strength.valueChanged.connect(self.state_changed.emit)

    # Add on 08172026 @apacheservice68 | editor encapsulating all reset actions
    def reset_ui(self):
        self.txt_face_image_path.setText("")
        self.chk_cuda.setChecked(False)
        self.chk_face_blur.setChecked(False)
        self.chk_bg_blur.setChecked(False)
        self.spin_face_blur_pct.setValue(0)
        self.spin_face_blur_strength.setValue(15)
        self.spin_bg_strength.setValue(181)
        self.cb_face_blur_type.setCurrentIndex(0)
        self.cb_face_blur_style.setCurrentIndex(0)
        self.widget_face_image.setVisible(False)

    def on_face_blur_type_changed(self):
        is_image = (self.cb_face_blur_type.currentData() == "Image")
        self.widget_face_image.setVisible(is_image)

    def browse_face_replacement_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Replacement Image", "", "Image Files (*.png *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.txt_face_image_path.setText(file_path)
            self.state_changed.emit()

    def get_state(self):
        return {
            'cuda': self.chk_cuda.isChecked(),
            'face_blur': self.chk_face_blur.isChecked(),
            'face_blur_pct': float(self.spin_face_blur_pct.value()),
            'face_blur_type': self.cb_face_blur_type.currentData(),
            'face_blur_image_path': self.txt_face_image_path.text(),
            'face_blur_style': self.cb_face_blur_style.currentData(),
            'face_blur_strength': self.spin_face_blur_strength.value(),
            'bg_blur': self.chk_bg_blur.isChecked(),
            'bg_blur_strength': self.spin_bg_strength.value()
        }

    def set_state(self, state):
        self.chk_cuda.setChecked(state.get('cuda', False))
        self.chk_face_blur.setChecked(state.get('face_blur', False))
        self.spin_face_blur_pct.setValue(int(state.get('face_blur_pct', 0)))
        self.cb_face_blur_type.setCurrentIndex(self.cb_face_blur_type.findData(state.get('face_blur_type')))
        self.txt_face_image_path.setText(state.get('face_blur_image_path', ''))
        self.cb_face_blur_style.setCurrentIndex(self.cb_face_blur_style.findData(state.get('face_blur_style')))
        self.spin_face_blur_strength.setValue(state.get('face_blur_strength', 15))
        self.chk_bg_blur.setChecked(state.get('bg_blur', False))
        self.spin_bg_strength.setValue(state.get('bg_blur_strength', 101))
        self.on_face_blur_type_changed() # Update visibility
