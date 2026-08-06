import sys
import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox, QFileDialog,
    QTextEdit, QMessageBox, QGroupBox, QFormLayout, QSlider,
    QTableWidget, QTableWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

import app.services.ffmpeg_service as ffmpeg_service
from app.ui.advance_watermark_tab import AdvanceWatermarkTab

class BasicCutTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.segments = []  # List of dict: {"start": float, "end": float}
        self.selected_segment_index = -1
        self.is_slider_moving = False
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Column: Video Player and Input Selection
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 3)

        # ---- Video Input Source ----
        file_group = QGroupBox("Video Input Source")
        file_layout = QHBoxLayout()
        self.lbl_video_path = QLabel("No video selected. Click 'Open Video' to select one.")
        self.lbl_video_path.setWordWrap(True)
        btn_open = QPushButton("Open Video")
        btn_open.clicked.connect(self.open_video)
        file_layout.addWidget(self.lbl_video_path, 1)
        file_layout.addWidget(btn_open)
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # ---- Video Player Widget ----
        player_group = QGroupBox("Video Player")
        player_layout = QVBoxLayout()
        
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(320)
        self.video_widget.setStyleSheet("background-color: black;")
        player_layout.addWidget(self.video_widget, 1)

        # Media Player components
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # Connections
        self.player.positionChanged.connect(self.on_player_position_changed)
        self.player.durationChanged.connect(self.on_player_duration_changed)

        # Playback timeline slider & Time Label
        timeline_layout = QHBoxLayout()
        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.slider_timeline.setRange(0, 0)
        self.slider_timeline.sliderPressed.connect(self.on_slider_pressed)
        self.slider_timeline.sliderReleased.connect(self.on_slider_released)
        self.slider_timeline.sliderMoved.connect(self.on_slider_moved)
        
        self.lbl_time = QLabel("00:00:00.000 / 00:00:00.000")
        timeline_layout.addWidget(self.slider_timeline, 1)
        timeline_layout.addWidget(self.lbl_time)
        player_layout.addLayout(timeline_layout)

        # Control Panel Buttons
        controls_layout = QHBoxLayout()
        self.btn_play_pause = QPushButton("Play")
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        
        self.btn_set_start = QPushButton("Set Start [")
        self.btn_set_start.setToolTip("Set segment start to current player position (Shortcut: [)")
        self.btn_set_start.clicked.connect(self.set_start_to_current)
        
        self.btn_set_end = QPushButton("Set End ]")
        self.btn_set_end.setToolTip("Set segment end to current player position (Shortcut: ])")
        self.btn_set_end.clicked.connect(self.set_end_to_current)
        
        self.btn_prev_seg = QPushButton("< Prev Segment")
        self.btn_prev_seg.clicked.connect(self.jump_to_prev_segment)
        
        self.btn_next_seg = QPushButton("Next Segment >")
        self.btn_next_seg.clicked.connect(self.jump_to_next_segment)

        self.btn_help_close = QPushButton("?")
        self.btn_help_close.setFixedWidth(28)
        self.btn_help_close.setToolTip("Nhấn Ctrl + W (Windows/Linux) hoặc Cmd + W (macOS) để đóng video hiện tại.")
        self.btn_help_close.clicked.connect(lambda: QMessageBox.information(self, "Trợ giúp", "Nhấn Ctrl + W (Windows/Linux) hoặc Cmd + W (macOS) để đóng video hiện tại."))

        controls_layout.addWidget(self.btn_play_pause)
        controls_layout.addWidget(self.btn_set_start)
        controls_layout.addWidget(self.btn_set_end)
        controls_layout.addWidget(self.btn_prev_seg)
        controls_layout.addWidget(self.btn_next_seg)
        controls_layout.addWidget(self.btn_help_close)
        player_layout.addLayout(controls_layout)
        player_group.setLayout(player_layout)
        left_layout.addWidget(player_group)

        # Right Column: Segments, Advanced features and Logs
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 2)

        # ---- Segments Management Panel ----
        segments_group = QGroupBox("Segments Manager")
        segments_layout = QVBoxLayout()

        # Segments Table
        self.table_segments = QTableWidget()
        self.table_segments.setColumnCount(4)
        self.table_segments.setHorizontalHeaderLabels(["Index", "Start", "End", "Duration"])
        self.table_segments.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_segments.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_segments.itemSelectionChanged.connect(self.on_segment_selection_changed)
        segments_layout.addWidget(self.table_segments)

        # Manual segment input fields
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

        # Action Buttons for Segments
        actions_layout = QHBoxLayout()
        btn_add_seg = QPushButton("Add Segment")
        btn_add_seg.clicked.connect(self.add_segment_action)
        
        btn_update_seg = QPushButton("Update Selected")
        btn_update_seg.clicked.connect(self.update_segment_action)
        
        btn_delete_seg = QPushButton("Delete Selected")
        btn_delete_seg.clicked.connect(self.delete_segment_action)

        actions_layout.addWidget(btn_add_seg)
        actions_layout.addWidget(btn_update_seg)
        actions_layout.addWidget(btn_delete_seg)
        segments_layout.addLayout(actions_layout)

        # Export Button specifically for cut segments
        export_layout = QHBoxLayout()
        self.btn_export = QPushButton("⚡ Export Segments (Lossless)")
        self.btn_export.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 13px; padding: 6px;")
        self.btn_export.clicked.connect(self.export_segments_action)
        export_layout.addWidget(self.btn_export)
        segments_layout.addLayout(export_layout)

        segments_group.setLayout(segments_layout)
        right_layout.addWidget(segments_group)

        # ---- Original Tools: Watermark & Merge ----
        adv_tools_group = QGroupBox("Advanced Tools")
        adv_tools_layout = QHBoxLayout()

        # Watermark Tool Sub-group
        watermark_sub = QGroupBox("Watermark (Re-encode)")
        watermark_sub_layout = QFormLayout()
        self.txt_watermark = QLineEdit("Mini LosslessCut")
        self.cb_position = QComboBox()
        self.cb_position.addItem("Top Left", "top_left")
        self.cb_position.addItem("Top Right", "top_right")
        self.cb_position.addItem("Bottom Left", "bottom_left")
        self.cb_position.addItem("Bottom Right", "bottom_right")
        btn_watermark = QPushButton("Watermark Video")
        btn_watermark.clicked.connect(self.watermark_video_action)
        watermark_sub_layout.addRow("Text:", self.txt_watermark)
        watermark_sub_layout.addRow("Pos:", self.cb_position)
        watermark_sub_layout.addRow(btn_watermark)
        watermark_sub.setLayout(watermark_sub_layout)
        adv_tools_layout.addWidget(watermark_sub)

        # Merge Tool Sub-group
        merge_sub = QGroupBox("Merge (No Re-encode)")
        merge_sub_layout = QVBoxLayout()
        btn_merge = QPushButton("Merge Videos...")
        btn_merge.clicked.connect(self.merge_videos_action)
        merge_sub_layout.addWidget(QLabel("Merge videos of same format."))
        merge_sub_layout.addWidget(btn_merge)
        merge_sub.setLayout(merge_sub_layout)
        adv_tools_layout.addWidget(merge_sub)

        adv_tools_group.setLayout(adv_tools_layout)
        right_layout.addWidget(adv_tools_group)

    def log(self, message: str):
        self.main_window.log(message)

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.avi *.mov *.flv);;All Files (*)"
        )
        if file_path:
            self.main_window.set_active_video(file_path)

    def set_video_path(self, file_path):
        self.lbl_video_path.setText(f"Selected: {os.path.basename(file_path)}\nFull Path: {file_path}")
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.segments = []
        self.update_segments_table()
        self.load_project_file(file_path)

    def reset_tab(self):
        self.lbl_video_path.setText("No video selected. Click 'Open Video' to select one.")
        self.player.setSource(QUrl())
        self.slider_timeline.setRange(0, 0)
        self.slider_timeline.setValue(0)
        self.lbl_time.setText("00:00:00.000 / 00:00:00.000")
        self.btn_play_pause.setText("Play")
        self.segments = []
        self.update_segments_table()
        self.txt_manual_start.clear()
        self.txt_manual_end.clear()

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play_pause.setText("Play")
        else:
            self.player.play()
            self.btn_play_pause.setText("Pause")

    def on_player_position_changed(self, position):
        if not self.is_slider_moving:
            self.slider_timeline.setValue(position)
        self.update_time_label()

    def on_player_duration_changed(self, duration):
        self.slider_timeline.setRange(0, duration)
        self.update_time_label()

    def update_time_label(self):
        pos_sec = self.player.position() / 1000.0
        dur_sec = self.player.duration() / 1000.0
        pos_str = ffmpeg_service.format_seconds_to_time(pos_sec)
        dur_str = ffmpeg_service.format_seconds_to_time(dur_sec)
        self.lbl_time.setText(f"{pos_str} / {dur_str}")

    def on_slider_pressed(self):
        self.is_slider_moving = True

    def on_slider_released(self):
        self.is_slider_moving = False
        self.player.setPosition(self.slider_timeline.value())

    def on_slider_moved(self, position):
        self.player.setPosition(position)

    def set_start_to_current(self):
        pos_sec = self.player.position() / 1000.0
        time_str = ffmpeg_service.format_seconds_to_time(pos_sec)
        self.txt_manual_start.setText(time_str)

    def set_end_to_current(self):
        pos_sec = self.player.position() / 1000.0
        time_str = ffmpeg_service.format_seconds_to_time(pos_sec)
        self.txt_manual_end.setText(time_str)

    def update_segments_table(self):
        self.table_segments.setRowCount(0)
        for i, seg in enumerate(self.segments):
            self.table_segments.insertRow(i)
            duration = seg["end"] - seg["start"]
            
            start_str = ffmpeg_service.format_seconds_to_time(seg["start"])
            end_str = ffmpeg_service.format_seconds_to_time(seg["end"])
            dur_str = ffmpeg_service.format_seconds_to_time(duration)
            
            self.table_segments.setItem(i, 0, QTableWidgetItem(f"Segment {i+1}"))
            self.table_segments.setItem(i, 1, QTableWidgetItem(start_str))
            self.table_segments.setItem(i, 2, QTableWidgetItem(end_str))
            self.table_segments.setItem(i, 3, QTableWidgetItem(dur_str))
        
        self.save_project_file()

    def on_segment_selection_changed(self):
        selected_ranges = self.table_segments.selectedRanges()
        if not selected_ranges:
            self.selected_segment_index = -1
            return
        
        self.selected_segment_index = selected_ranges[0].topRow()
        if 0 <= self.selected_segment_index < len(self.segments):
            seg = self.segments[self.selected_segment_index]
            self.txt_manual_start.setText(ffmpeg_service.format_seconds_to_time(seg["start"]))
            self.txt_manual_end.setText(ffmpeg_service.format_seconds_to_time(seg["end"]))
            self.player.setPosition(int(seg["start"] * 1000))

    def add_segment_action(self):
        start_str = self.txt_manual_start.text().strip()
        end_str = self.txt_manual_end.text().strip()
        
        if not start_str or not end_str:
            QMessageBox.warning(self, "Warning", "Please specify both Start and End times.")
            return
            
        start_sec = ffmpeg_service.parse_time_to_seconds(start_str)
        end_sec = ffmpeg_service.parse_time_to_seconds(end_str)
        
        if start_sec >= end_sec:
            QMessageBox.warning(self, "Warning", "Start time must be less than End time.")
            return

        self.segments.append({"start": start_sec, "end": end_sec})
        self.segments.sort(key=lambda s: s["start"])
        self.update_segments_table()
        self.log(f"Added segment: {start_str} - {end_str}")

    def update_segment_action(self):
        if self.selected_segment_index < 0 or self.selected_segment_index >= len(self.segments):
            QMessageBox.warning(self, "Warning", "Please select a segment from the table first.")
            return
            
        start_str = self.txt_manual_start.text().strip()
        end_str = self.txt_manual_end.text().strip()
        
        if not start_str or not end_str:
            QMessageBox.warning(self, "Warning", "Please specify both Start and End times.")
            return
            
        start_sec = ffmpeg_service.parse_time_to_seconds(start_str)
        end_sec = ffmpeg_service.parse_time_to_seconds(end_str)
        
        if start_sec >= end_sec:
            QMessageBox.warning(self, "Warning", "Start time must be less than End time.")
            return
            
        self.segments[self.selected_segment_index] = {"start": start_sec, "end": end_sec}
        self.segments.sort(key=lambda s: s["start"])
        self.update_segments_table()
        self.log(f"Updated segment to: {start_str} - {end_str}")

    def delete_segment_action(self):
        if self.selected_segment_index < 0 or self.selected_segment_index >= len(self.segments):
            QMessageBox.warning(self, "Warning", "Please select a segment from the table first.")
            return
            
        deleted = self.segments.pop(self.selected_segment_index)
        self.update_segments_table()
        self.log(f"Deleted segment: {ffmpeg_service.format_seconds_to_time(deleted['start'])} - {ffmpeg_service.format_seconds_to_time(deleted['end'])}")

    def jump_to_prev_segment(self):
        if not self.segments:
            return
        
        current_pos_sec = self.player.position() / 1000.0
        target_seg = None
        for seg in reversed(self.segments):
            if seg["start"] < current_pos_sec - 0.5:
                target_seg = seg
                break
        
        if target_seg is None:
            target_seg = self.segments[-1]
            
        self.player.setPosition(int(target_seg["start"] * 1000))
        self.log(f"Jumped to segment start: {ffmpeg_service.format_seconds_to_time(target_seg['start'])}")

    def jump_to_next_segment(self):
        if not self.segments:
            return
            
        current_pos_sec = self.player.position() / 1000.0
        target_seg = None
        for seg in self.segments:
            if seg["start"] > current_pos_sec + 0.5:
                target_seg = seg
                break
                
        if target_seg is None:
            target_seg = self.segments[0]
            
        self.player.setPosition(int(target_seg["start"] * 1000))
        self.log(f"Jumped to segment start: {ffmpeg_service.format_seconds_to_time(target_seg['start'])}")

    def get_project_file_path(self, video_path=None) -> str:
        v_path = video_path or self.main_window.selected_video_path
        if not v_path:
            return ""
        base_dir = os.path.dirname(v_path)
        base_name = os.path.basename(v_path)
        return os.path.join(base_dir, f"{base_name}.project.json")

    def save_project_file(self):
        project_path = self.get_project_file_path()
        if not project_path:
            return
            
        data = {
            "video_path": self.main_window.selected_video_path,
            "segments": self.segments
        }
        try:
            with open(project_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.log(f"Project auto-saved: {os.path.basename(project_path)}")
        except Exception as e:
            self.log(f"Failed to auto-save project: {str(e)}")

    def load_project_file(self, video_path):
        project_path = self.get_project_file_path(video_path)
        if not project_path or not os.path.exists(project_path):
            return
            
        try:
            with open(project_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.segments = data.get("segments", [])
            self.update_segments_table()
            self.log(f"Project loaded successfully: {os.path.basename(project_path)} ({len(self.segments)} segments)")
        except Exception as e:
            self.log(f"Failed to load project file: {str(e)}")

    def export_segments_action(self):
        if not self.main_window.selected_video_path:
            QMessageBox.warning(self, "Warning", "Please select an input video first!")
            return
            
        if not self.segments:
            QMessageBox.warning(self, "Warning", "No segments defined to export.")
            return

        dest_dir = QFileDialog.getExistingDirectory(
            self, "Select Directory to Save Exported Segments", os.path.dirname(self.main_window.selected_video_path)
        )
        if not dest_dir:
            return

        self.log(f"Starting export of {len(self.segments)} segments...")
        
        video_name = os.path.basename(self.main_window.selected_video_path)
        base_name, ext = os.path.splitext(video_name)
        
        success_count = 0
        for i, seg in enumerate(self.segments):
            start_str = ffmpeg_service.format_seconds_to_time(seg["start"], include_ms=False)
            end_str = ffmpeg_service.format_seconds_to_time(seg["end"], include_ms=False)
            
            safe_start = start_str.replace(":", "-")
            safe_end = end_str.replace(":", "-")
            
            output_filename = f"{base_name}_{safe_start}_{safe_end}{ext}"
            output_path = os.path.join(dest_dir, output_filename)
            
            self.log(f"Exporting Segment {i+1}: {start_str} to {end_str} -> {output_filename}")
            
            try:
                ffmpeg_service.cut_video(self.main_window.selected_video_path, output_path, start_str, end_str)
                success_count += 1
                self.log(f"Exported: {output_filename}")
            except Exception as e:
                self.log(f"Error exporting Segment {i+1}: {str(e)}")
                
        if success_count == len(self.segments):
            QMessageBox.information(self, "Export Finished", f"Successfully exported all {success_count} segments!")
        else:
            QMessageBox.warning(self, "Export Finished with issues", f"Exported {success_count}/{len(self.segments)} segments. Check logs.")

    def watermark_video_action(self):
        if not self.main_window.selected_video_path:
            QMessageBox.warning(self, "Warning", "Please select an input video first!")
            return

        text = self.txt_watermark.text().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter watermark text.")
            return

        position = self.cb_position.currentData()
        
        ext = os.path.splitext(self.main_window.selected_video_path)[1]
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Watermarked Video As", f"watermark_output{ext}", f"Video Files (*{ext});;All Files (*)"
        )
        if not output_path:
            return

        self.log(f"Adding watermark '{text}' at position '{position}'...")
        try:
            ffmpeg_service.watermark_video(self.main_window.selected_video_path, output_path, text, position)
            self.log(f"Successfully saved watermarked video to: {output_path}")
            QMessageBox.information(self, "Success", "Watermark added successfully!")
        except Exception as e:
            self.log(f"Error watermarking video: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to watermark video:\n{str(e)}")

    def merge_videos_action(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files to Merge", "", "Video Files (*.mp4 *.mkv *.avi *.mov *.flv);;All Files (*)"
        )
        if not file_paths:
            return
        if len(file_paths) < 2:
            QMessageBox.warning(self, "Warning", "Please select at least 2 video files to merge.")
            return

        first_file = file_paths[0]
        ext = os.path.splitext(first_file)[1]
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged Video As", f"merged_output{ext}", f"Video Files (*{ext});;All Files (*)"
        )
        if not output_path:
            return

        self.log(f"Merging {len(file_paths)} videos...")
        try:
            ffmpeg_service.merge_videos(file_paths, output_path)
            self.log(f"Successfully merged videos into: {output_path}")
            QMessageBox.information(self, "Success", "Videos merged successfully!")
        except Exception as e:
            self.log(f"Error merging videos: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to merge videos:\n{str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_video_path = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Mini LosslessCut - Professional Edition with AI")
        self.resize(1200, 850)

        # Main vertical layout containing tab widget and log output
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Tab Widget
        self.tabs = QTabWidget()
        self.basic_tab = BasicCutTab(self)
        self.advance_tab = AdvanceWatermarkTab(self)
        
        self.advance_tab.log_message.connect(self.log)

        self.tabs.addTab(self.basic_tab, "Basic Cut / Watermark")
        self.tabs.addTab(self.advance_tab, "Advance Watermark & AI")
        main_layout.addWidget(self.tabs, 1)

        # Shared Log Console on bottom
        log_group = QGroupBox("Global Log Console")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

    def set_active_video(self, video_path):
        self.selected_video_path = video_path
        self.log(f"Loaded active video: {video_path}")
        self.basic_tab.set_video_path(video_path)
        self.advance_tab.set_video_path(video_path)

    def close_video(self):
        self.selected_video_path = ""
        self.log("Closing active video and resetting state.")
        self.basic_tab.reset_tab()
        self.advance_tab.reset_tab()

    def log(self, message: str):
        self.log_output.append(message)

    # Global keyboard listener for hotkeys
    def keyPressEvent(self, event):
        # Check Ctrl+W or Cmd+W to close video globally
        is_ctrl_w = (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_W
        is_cmd_w = (event.modifiers() & Qt.KeyboardModifier.MetaModifier) and event.key() == Qt.Key.Key_W
        if is_ctrl_w or is_cmd_w:
            self.close_video()
            return

        # Only route hotkeys to Basic Cut tab if it is the currently active tab
        if self.tabs.currentWidget() == self.basic_tab:
            if event.key() == Qt.Key.Key_BracketLeft:
                self.basic_tab.set_start_to_current()
            elif event.key() == Qt.Key.Key_BracketRight:
                self.basic_tab.set_end_to_current()
            elif event.key() == Qt.Key.Key_Space:
                # Avoid space trigger during focus on text fields
                focused = self.focusWidget()
                if not isinstance(focused, QLineEdit):
                    self.basic_tab.toggle_play_pause()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
