from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QLineEdit, 
    QPushButton, QLabel, QAbstractItemView, QTableWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from app.core.helpers import format_ms_to_timecode, timecode_to_ms

class SegmentManagerWidget(QWidget):
    state_changed = pyqtSignal()

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.selected_segment_index = -1
        self.init_ui()

    def init_ui(self):
        segment_group = QGroupBox("Segments Manager")
        segments_layout = QVBoxLayout()

        self.table_segments = QTableWidget()
        self.table_segments.setColumnCount(4)
        self.table_segments.setHorizontalHeaderLabels(["Index", "Start", "End", "Duration"])
        self.table_segments.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_segments.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_segments.itemSelectionChanged.connect(self.on_segment_selected)
        segments_layout.addWidget(self.table_segments)

        manual_layout = QHBoxLayout()
        self.txt_manual_start = QLineEdit()
        self.txt_manual_start.setPlaceholderText("Start (e.g. 00:01:15.123)")
        self.txt_manual_end = QLineEdit()
        self.txt_manual_end.setPlaceholderText("End (e.g. 00:02:30.456)")
        
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

        segment_group.setLayout(segments_layout)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(segment_group)
        self.setLayout(main_layout)
        
        # Connect signals
        self.btn_add_seg.clicked.connect(self.add_segment)
        self.btn_update_seg.clicked.connect(self.update_selected_segment)
        self.btn_delete_seg.clicked.connect(self.delete_selected_segment)

    def on_segment_selected(self):
        selected_items = self.table_segments.selectedItems()
        if not selected_items:
            self.selected_segment_index = -1
            return

        self.selected_segment_index = selected_items[0].row()
        start_time = self.table_segments.item(self.selected_segment_index, 1).text()
        end_time = self.table_segments.item(self.selected_segment_index, 2).text()
        self.txt_manual_start.setText(start_time)
        self.txt_manual_end.setText(end_time)

    def get_all_segments(self):
        segments = []
        for i in range(self.table_segments.rowCount()):
            start_ms = timecode_to_ms(self.table_segments.item(i, 1).text())
            end_ms = timecode_to_ms(self.table_segments.item(i, 2).text())
            segments.append({"start": start_ms / 1000.0, "end": end_ms / 1000.0})
        return segments

    def set_start_time(self, ms_time):
        self.txt_manual_start.setText(format_ms_to_timecode(ms_time))

    def set_end_time(self, ms_time):
        self.txt_manual_end.setText(format_ms_to_timecode(ms_time))

    def add_segment(self):
        start_time_str = self.txt_manual_start.text()
        end_time_str = self.txt_manual_end.text()

        if not start_time_str or not end_time_str:
            # TODO: Show some error to user
            return
        
        try:
            start_ms = timecode_to_ms(start_time_str)
            end_ms = timecode_to_ms(end_time_str)
        except ValueError:
            # TODO: Show some error to user
            return

        if start_ms >= end_ms:
             # TODO: Show some error to user
            return

        row_position = self.table_segments.rowCount()
        self.table_segments.insertRow(row_position)
        
        duration_ms = end_ms - start_ms
        
        self.table_segments.setItem(row_position, 0, QTableWidgetItem(str(row_position + 1)))
        self.table_segments.setItem(row_position, 1, QTableWidgetItem(format_ms_to_timecode(start_ms)))
        self.table_segments.setItem(row_position, 2, QTableWidgetItem(format_ms_to_timecode(end_ms)))
        self.table_segments.setItem(row_position, 3, QTableWidgetItem(format_ms_to_timecode(duration_ms)))
        
        self.txt_manual_start.clear()
        self.txt_manual_end.clear()
        self.table_segments.selectRow(row_position)
        self.state_changed.emit()

    def update_selected_segment(self):
        if self.selected_segment_index < 0:
            return

        start_time_str = self.txt_manual_start.text()
        end_time_str = self.txt_manual_end.text()

        try:
            start_ms = timecode_to_ms(start_time_str)
            end_ms = timecode_to_ms(end_time_str)
        except ValueError:
            return

        if start_ms >= end_ms:
            return
        
        duration_ms = end_ms - start_ms

        self.table_segments.setItem(self.selected_segment_index, 1, QTableWidgetItem(format_ms_to_timecode(start_ms)))
        self.table_segments.setItem(self.selected_segment_index, 2, QTableWidgetItem(format_ms_to_timecode(end_ms)))
        self.table_segments.setItem(self.selected_segment_index, 3, QTableWidgetItem(format_ms_to_timecode(duration_ms)))
        self.state_changed.emit()

    def delete_selected_segment(self):
        if self.selected_segment_index < 0:
            return
        
        self.table_segments.removeRow(self.selected_segment_index)
        
        # Renumber indices
        for i in range(self.table_segments.rowCount()):
            self.table_segments.item(i, 0).setText(str(i + 1))

        self.selected_segment_index = -1
        self.txt_manual_start.clear()
        self.txt_manual_end.clear()
        self.table_segments.clearSelection()
        self.state_changed.emit()

    def get_selected_segment_times(self):
        if self.selected_segment_index < 0 or self.selected_segment_index >= self.table_segments.rowCount():
            return None, None
        start_item = self.table_segments.item(self.selected_segment_index, 1)
        end_item = self.table_segments.item(self.selected_segment_index, 2)
        if start_item and end_item:
            return timecode_to_ms(start_item.text()), timecode_to_ms(end_item.text())
        return None, None

    def select_prev_segment(self):
        if self.table_segments.rowCount() == 0: return None
        current_row = self.table_segments.currentRow()
        if current_row <= 0:
            new_row = self.table_segments.rowCount() - 1
        else:
            new_row = current_row - 1
        self.table_segments.selectRow(new_row)
        return self.get_selected_segment_times()

    def reset_ui(self):
        self.table_segments.setRowCount(0)
        self.txt_manual_start.setText("00:00:00.000")
        self.txt_manual_end.setText("00:00:00.000")
        self.selected_segment_index = -1
        self.table_segments.clearSelection()

    def set_all_segments(self, segments):
        self.table_segments.setRowCount(0)
        for i, seg in enumerate(segments):
            start_ms = int(seg["start"] * 1000)
            end_ms = int(seg["end"] * 1000)
            duration_ms = end_ms - start_ms

            row_position = self.table_segments.rowCount()
            self.table_segments.insertRow(row_position)
            self.table_segments.setItem(row_position, 0, QTableWidgetItem(str(i + 1)))
            self.table_segments.setItem(row_position, 1, QTableWidgetItem(format_ms_to_timecode(start_ms)))
            self.table_segments.setItem(row_position, 2, QTableWidgetItem(format_ms_to_timecode(end_ms)))
            self.table_segments.setItem(row_position, 3, QTableWidgetItem(format_ms_to_timecode(duration_ms)))
        self.state_changed.emit()

    def select_next_segment(self):
        if self.table_segments.rowCount() == 0: return None
        current_row = self.table_segments.currentRow()
        if current_row >= self.table_segments.rowCount() - 1:
            new_row = 0
        else:
            new_row = current_row + 1
        self.table_segments.selectRow(new_row)
        return self.get_selected_segment_times()


