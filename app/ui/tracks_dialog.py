from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QHeaderView, QPushButton, QCheckBox, 
    QTableWidgetItem, QDialogButtonBox, QGroupBox, QHBoxLayout, QAbstractItemView
)

class TracksDialog(QDialog):
    """A dialog for managing video/audio tracks and their metadata."""
    
    # Signal emitted when changes are applied
    changes_applied = pyqtSignal()

    def __init__(self, tracks, parent=None):
        super().__init__(parent)
        self.tracks = tracks
        # Deep copy for temporary edits
        self.temp_tracks = [track.copy() for track in tracks]
        self.selected_track_index = -1
        
        self.setWindowTitle("Track Management")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.connect_signals()
        
        if self.tracks:
            self.tracks_table.selectRow(0)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Main tracks table
        tracks_group = QGroupBox("Available Tracks")
        tracks_layout = QVBoxLayout()
        self.tracks_table = QTableWidget()
        self.tracks_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tracks_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tracks_table.setColumnCount(5)
        self.tracks_table.setHorizontalHeaderLabels(["Enabled", "ID", "Type", "Codec", "Metadata"])
        self.tracks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tracks_table.verticalHeader().setVisible(False)
        self.populate_tracks_table()
        tracks_layout.addWidget(self.tracks_table)
        tracks_group.setLayout(tracks_layout)
        main_layout.addWidget(tracks_group)
        
        # Metadata editor for selected track
        metadata_group = QGroupBox("Metadata for selected track")
        metadata_layout = QVBoxLayout()
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Key", "Value"])
        self.metadata_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        metadata_layout.addWidget(self.metadata_table)
        
        self.btn_add_meta = QPushButton("Add Metadata Field")
        metadata_layout.addWidget(self.btn_add_meta)
        metadata_group.setLayout(metadata_layout)
        main_layout.addWidget(metadata_group)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)

    def connect_signals(self):
        self.tracks_table.itemSelectionChanged.connect(self.on_track_selection_changed)
        self.btn_add_meta.clicked.connect(self.add_metadata_row)
        self.button_box.accepted.connect(self.save_changes)
        self.button_box.rejected.connect(self.reject)

    def populate_tracks_table(self):
        self.tracks_table.setRowCount(len(self.temp_tracks))
        for i, track in enumerate(self.temp_tracks):
            # Enabled checkbox
            enabled_check = QCheckBox()
            enabled_check.setChecked(track.get("enabled", True))
            enabled_check.toggled.connect(lambda state, idx=i: self.toggle_track_enabled(idx, state))
            self.tracks_table.setCellWidget(i, 0, enabled_check)

            # Other track info
            self.tracks_table.setItem(i, 1, QTableWidgetItem(str(track.get("index"))))
            self.tracks_table.setItem(i, 2, QTableWidgetItem(track.get("codec_type")))
            self.tracks_table.setItem(i, 3, QTableWidgetItem(track.get("codec_name")))
            
            # Metadata summary
            tags = track.get("tags", {})
            meta_summary = ", ".join([f"{k}: {v}" for k, v in tags.items()])
            self.tracks_table.setItem(i, 4, QTableWidgetItem(meta_summary))
            self.tracks_table.item(i, 4).setFlags(self.tracks_table.item(i, 4).flags() & ~Qt.ItemFlag.ItemIsEditable)

    def on_track_selection_changed(self):
        # First, save any pending metadata edits for the currently selected track
        # before changing the selection.
        self.update_metadata_from_table()

        selected_rows = self.tracks_table.selectionModel().selectedRows()
        if not selected_rows:
            self.selected_track_index = -1
            self.metadata_table.setRowCount(0)
            return

        new_selection_index = selected_rows[0].row()
        # Do not proceed if selection hasn't actually changed
        if self.selected_track_index == new_selection_index:
            return
            
        self.selected_track_index = new_selection_index
        self.populate_metadata_table()

    def populate_metadata_table(self):
        if self.selected_track_index == -1:
            self.metadata_table.setRowCount(0)
            return

        track = self.temp_tracks[self.selected_track_index]
        tags = track.get("tags", {})
        
        self.metadata_table.setRowCount(len(tags))
        for i, (key, value) in enumerate(tags.items()):
            self.metadata_table.setItem(i, 0, QTableWidgetItem(key))
            self.metadata_table.setItem(i, 1, QTableWidgetItem(value))
            
    def add_metadata_row(self):
        if self.selected_track_index == -1:
            return
        
        row_count = self.metadata_table.rowCount()
        self.metadata_table.insertRow(row_count)
        self.metadata_table.setItem(row_count, 0, QTableWidgetItem("new_key"))
        self.metadata_table.setItem(row_count, 1, QTableWidgetItem("new_value"))

    def toggle_track_enabled(self, index, state):
        if 0 <= index < len(self.temp_tracks):
            self.temp_tracks[index]["enabled"] = bool(state)

    def save_changes(self):
        """Commit changes from UI back to the original track list."""
        # First, save any pending metadata edits for the last selected track
        self.update_metadata_from_table()

        # Update the original tracks list
        for i, temp_track in enumerate(self.temp_tracks):
            self.tracks[i].update(temp_track)
        
        self.changes_applied.emit()
        self.accept()

    def update_metadata_from_table(self):
        if self.selected_track_index == -1:
            return

        new_tags = {}
        for i in range(self.metadata_table.rowCount()):
            key_item = self.metadata_table.item(i, 0)
            value_item = self.metadata_table.item(i, 1)
            if key_item and value_item and key_item.text():
                new_tags[key_item.text()] = value_item.text()
        
        self.temp_tracks[self.selected_track_index]["tags"] = new_tags

