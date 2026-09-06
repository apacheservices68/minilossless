from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QSlider, QSpinBox, QListWidget, QGroupBox,
    QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class TextOverlayEditorWidget(QWidget):
    add_text_overlay = pyqtSignal()
    delete_selected_text = pyqtSignal()
    selection_changed = pyqtSignal(int)
    properties_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        text_group = QGroupBox("Canva-Style Multi-Text Overlays")
        text_layout = QVBoxLayout()
        
        edit_form = QFormLayout()
        self.txt_overlay_text = QLineEdit("My Watermark")
        self.txt_overlay_text.textChanged.connect(self.on_properties_changed)
        
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 200)
        self.spin_font_size.setValue(32)
        self.spin_font_size.valueChanged.connect(self.on_properties_changed)
        
        self.slider_rotation = QSlider(Qt.Orientation.Horizontal)
        self.slider_rotation.setRange(-360, 360)
        self.slider_rotation.setValue(0)
        self.slider_rotation.valueChanged.connect(self.on_properties_changed)
        
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(100)
        self.slider_opacity.valueChanged.connect(self.on_properties_changed)
        
        edit_form.addRow("Text Content:", self.txt_overlay_text)
        edit_form.addRow("Font Size (px):", self.spin_font_size)
        edit_form.addRow("Rotation Angle (°):", self.slider_rotation)
        edit_form.addRow("Opacity (%):", self.slider_opacity)
        text_layout.addLayout(edit_form)
        
        self.list_overlays = QListWidget()
        self.list_overlays.currentRowChanged.connect(self.selection_changed.emit)
        text_layout.addWidget(self.list_overlays)
        
        buttons_layout = QHBoxLayout()
        btn_add_text = QPushButton("Add New Text Overlay")
        btn_add_text.setStyleSheet("background-color: #008CBA; color: white;")
        btn_add_text.clicked.connect(self.add_text_overlay.emit)
        
        btn_delete_text = QPushButton("Delete Selected Text")
        btn_delete_text.setStyleSheet("background-color: #f44336; color: white;")
        btn_delete_text.clicked.connect(self.delete_selected_text.emit)
        
        buttons_layout.addWidget(btn_add_text)
        buttons_layout.addWidget(btn_delete_text)
        text_layout.addLayout(buttons_layout)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

    def on_properties_changed(self):
        self.properties_changed.emit()

    def get_properties(self):
        return {
            'text': self.txt_overlay_text.text(),
            'font_size': self.spin_font_size.value(),
            'angle': float(self.slider_rotation.value()),
            'opacity': self.slider_opacity.value() / 100.0
        }

    def set_properties(self, text, font_size, angle, opacity):
        self.txt_overlay_text.blockSignals(True)
        self.spin_font_size.blockSignals(True)
        self.slider_rotation.blockSignals(True)
        self.slider_opacity.blockSignals(True)

        self.txt_overlay_text.setText(text)
        self.spin_font_size.setValue(font_size)
        self.slider_rotation.setValue(int(angle))
        self.slider_opacity.setValue(int(opacity * 100))

        self.txt_overlay_text.blockSignals(False)
        self.spin_font_size.blockSignals(False)
        self.slider_rotation.blockSignals(False)
        self.slider_opacity.blockSignals(False)

    # Add on 08172026 @apacheservice68 | editor encapsulating all reset actions
    def reset_ui(self):
        self.list_overlays.clear()
        self.selected_item = None
        self.txt_overlay_text.setText("")
        self.spin_font_size.setValue(32)
        self.slider_rotation.setValue(0)
        self.slider_opacity.setValue(100)

    def add_overlay_item(self, name):
        self.list_overlays.addItem(name)

    def clear_overlays(self):
        self.list_overlays.clear()

    def set_selected_row(self, index):
        self.list_overlays.setCurrentRow(index)

    def get_selected_row(self):
        return self.list_overlays.currentRow()

    def take_item(self, index):
        return self.list_overlays.takeItem(index)

    def count(self):
        return self.list_overlays.count()
    
    def item(self, row):
        return self.list_overlays.item(row)
