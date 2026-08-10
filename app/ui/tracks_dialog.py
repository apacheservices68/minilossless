
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QHeaderView, QPushButton, QCheckBox, QTableWidgetItem
)

class TracksDialog(QDialog):
    def __init__(self, tracks, parent=None):
        super().__init__(parent)
        self.tracks = tracks
        self.setWindowTitle("Track Management")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Enabled", "ID", "Type", "Codec"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.populate_table()
        layout.addWidget(self.table)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def populate_table(self):
        self.table.setRowCount(len(self.tracks))
        for i, track in enumerate(self.tracks):
            enabled_check = QCheckBox()
            enabled_check.setChecked(track.get("disposition", {}).get("default", 0) == 1)
            enabled_check.toggled.connect(lambda state, t=track: self.toggle_track(t, state))
            
            self.table.setCellWidget(i, 0, enabled_check)
            self.table.setItem(i, 1, QTableWidgetItem(str(track.get("index"))))
            self.table.setItem(i, 2, QTableWidgetItem(track.get("codec_type")))
            self.table.setItem(i, 3, QTableWidgetItem(track.get("codec_name")))

    def toggle_track(self, track, state):
        if "disposition" not in track:
            track["disposition"] = {}
        track["disposition"]["default"] = 1 if state else 0
