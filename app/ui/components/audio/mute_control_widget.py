import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox, QDoubleSpinBox,
    QSlider, QFileDialog, QHBoxLayout, QLabel, QSizePolicy, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.core import audio_constants as const

class MuteControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.beep_file_path = None

        layout = QVBoxLayout(self)
        mute_group = QGroupBox("Mute / Audio Controls")
        mute_layout = QVBoxLayout()

        # === Main Checkboxes ===
        self.mute_all_checkbox = QCheckBox("Mute Video Completely")
        self.smart_mute_checkbox = QCheckBox("Enable Smart AI Mute")

        mute_layout.addWidget(self.mute_all_checkbox)
        mute_layout.addWidget(self.smart_mute_checkbox)

        # === AI Controls Widget ===
        self.ai_controls_widget = QWidget()
        ai_controls_layout = QVBoxLayout(self.ai_controls_widget)
        ai_controls_layout.setContentsMargins(20, 0, 0, 0)

        self.threshold_slider, self.threshold_spinbox = self._create_slider_spinbox(
            "Threshold", const.THRESHOLD_MIN, const.THRESHOLD_MAX, const.THRESHOLD_DEFAULT, 3
        )
        ai_controls_layout.addLayout(self._create_labeled_control("Threshold:", self.threshold_slider, self.threshold_spinbox))

        self.duration_slider, self.duration_spinbox = self._create_slider_spinbox(
            "Duration", const.DURATION_MIN, const.DURATION_MAX, const.DURATION_DEFAULT, 3
        )
        ai_controls_layout.addLayout(self._create_labeled_control("Min Duration (s):", self.duration_slider, self.duration_spinbox))

        self.padding_slider, self.padding_spinbox = self._create_slider_spinbox(
            "Padding", const.PADDING_MIN, const.PADDING_MAX, const.PADDING_DEFAULT, 3
        )
        ai_controls_layout.addLayout(self._create_labeled_control("Padding (s):", self.padding_slider, self.padding_spinbox))

        # === Beep Sound Replacement ===
        self.beep_checkbox = QCheckBox("Replace Muted Audio with Beep Sound")
        ai_controls_layout.addWidget(self.beep_checkbox)

        self.file_picker_widget = QWidget()
        file_picker_layout = QHBoxLayout(self.file_picker_widget)
        file_picker_layout.setContentsMargins(20, 0, 0, 0)
        self.beep_file_label = QLabel("No file selected.")
        self.beep_file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.browse_button = QPushButton("Browse...")

        file_picker_layout.addWidget(self.beep_file_label)
        file_picker_layout.addWidget(self.browse_button)
        ai_controls_layout.addWidget(self.file_picker_widget)

        mute_layout.addWidget(self.ai_controls_widget)

        mute_group.setLayout(mute_layout)
        layout.addWidget(mute_group)

        # === Connections ===
        self.mute_all_checkbox.toggled.connect(self._update_ui_states)
        self.smart_mute_checkbox.toggled.connect(self._update_ui_states)
        self.beep_checkbox.toggled.connect(self._update_ui_states)
        self.browse_button.clicked.connect(self._browse_beep_file)

        # Initial state setup
        self._update_ui_states()

    def _create_slider_spinbox(self, name, min_val, max_val, default_val, decimals):
        multiplier = 10 ** decimals
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(int(min_val * multiplier))
        slider.setMaximum(int(max_val * multiplier))
        slider.setValue(int(default_val * multiplier))

        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSingleStep(1 / multiplier)
        spinbox.setValue(default_val)
        spinbox.setDecimals(decimals)

        slider.valueChanged.connect(lambda value: spinbox.setValue(value / float(multiplier)))
        spinbox.valueChanged.connect(lambda value: slider.setValue(int(value * multiplier)))

        return slider, spinbox

    def _create_labeled_control(self, label_text, slider, spinbox):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(120)
        layout.addWidget(label)
        layout.addWidget(slider)
        layout.addWidget(spinbox)
        return layout

    def _update_ui_states(self):
        sender = self.sender()

        is_mute_all = self.mute_all_checkbox.isChecked()
        is_smart_mute = self.smart_mute_checkbox.isChecked()
        is_beep_replace = self.beep_checkbox.isChecked()

        # Mutual exclusion logic
        if sender == self.mute_all_checkbox and is_mute_all:
            self.smart_mute_checkbox.setChecked(False)

        if sender == self.smart_mute_checkbox and is_smart_mute:
            self.mute_all_checkbox.setChecked(False)

        # Update visibility based on new state
        is_mute_all = self.mute_all_checkbox.isChecked()
        is_smart_mute = self.smart_mute_checkbox.isChecked()

        self.smart_mute_checkbox.setVisible(not is_mute_all)
        self.mute_all_checkbox.setVisible(not is_smart_mute)
        self.ai_controls_widget.setVisible(is_smart_mute)
        self.file_picker_widget.setVisible(is_smart_mute and is_beep_replace)

    def _browse_beep_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Beep Audio File",
            "",
            "Audio Files (*.wav *.mp3)"
        )

        if not file_path:
            return

        # Validate file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 1:
            QMessageBox.warning(
                self, "File Too Large",
                f"The selected file is {file_size_mb:.2f} MB. Please choose a file smaller than 1 MB."
            )
            return

        self.beep_file_path = file_path
        self.beep_file_label.setText(os.path.basename(file_path))
        self.beep_file_label.setToolTip(file_path)

    def get_settings(self) -> dict:
        """Returns a dictionary of the current settings."""
        return {
            "mute_all": self.mute_all_checkbox.isChecked(),
            "smart_mute": self.smart_mute_checkbox.isChecked(),
            "threshold": self.threshold_spinbox.value(),
            "min_duration": self.duration_spinbox.value(),
            "padding": self.padding_spinbox.value(),
            "replace_beep": self.beep_checkbox.isChecked(),
            "beep_file": self.beep_file_path
        }
