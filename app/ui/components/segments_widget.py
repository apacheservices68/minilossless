# app/ui/components/segments_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QLineEdit, 
    QPushButton, QComboBox, QCheckBox, QLabel, QAbstractItemView
)

class SegmentsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.selected_segment_index = -1
        self.init_ui()

    def init_ui(self):
        segments_group = QGroupBox("Segments Manager")
        segments_layout = QVBoxLayout()

        self.table_segments = QTableWidget()
        self.table_segments.setColumnCount(4)
        self.table_segments.setHorizontalHeaderLabels(["Index", "Start", "End", "Duration"])
        self.table_segments.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_segments.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        segments_layout.addWidget(self.table_segments)

        manual_layout = QHBoxLayout()
        self.txt_manual_start = QLineEdit()
        self.txt_manual_start.setPlaceholderText("Start (e.g. 00:01:15)")
        self.txt_manual_end = QLineEdit()
        self.txt_manual_end.setPlaceholderText("End (e.g. 00:02:30)")
        
        manual_layout.addWidget(QLabel("Start:"))
        manual_layout.addWidget(self.txt_manual_start)
        manual_layout.addWidget(QLabel("End:"))
        manual_layout.addWidget(self.txt_manual_end)
        segments_layout.addLayout(manual_layout)

        actions_layout = QHBoxLayout()
        self.btn_add_seg = QPushButton("Add Segment")
        self.btn_update_seg = QPushButton("Update Selected")
        self.btn_delete_seg = QPushButton("Delete Selected")

        actions_layout.addWidget(self.btn_add_seg)
        actions_layout.addWidget(self.btn_update_seg)
        actions_layout.addWidget(self.btn_delete_seg)
        segments_layout.addLayout(actions_layout)

        export_layout = QHBoxLayout()
        self.btn_export = QPushButton("⚡ Export Segments (Lossless)")
        self.btn_export.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 13px; padding: 6px;")
        self.cb_export_mode = QComboBox()
        self.cb_export_mode.addItem("Separate files", "separate")
        self.cb_export_mode.addItem("Merge & Separate", "merge")

        export_layout.addWidget(self.btn_export)
        export_layout.addWidget(self.cb_export_mode)
        segments_layout.addLayout(export_layout)

        cleanup_layout = QHBoxLayout()
        self.chk_cleanup = QCheckBox("Delete separate files after merging")
        self.chk_cleanup.setChecked(True)
        self.chk_cleanup.setEnabled(False)
        cleanup_layout.addWidget(self.chk_cleanup)
        segments_layout.addLayout(cleanup_layout)

        self.smart_cut_checkbox = QCheckBox("Enable Smart Cut (Exact Cut)")
        segments_layout.addWidget(self.smart_cut_checkbox)

        segments_group.setLayout(segments_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(segments_group)
        self.setLayout(main_layout)

        # Connect signals
        self.btn_add_seg.clicked.connect(self.main_window.add_segment_action)
        self.btn_update_seg.clicked.connect(self.main_window.update_segment_action)
        self.btn_delete_seg.clicked.connect(self.main_window.delete_segment_action)


