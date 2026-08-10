import sys
import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox, QFileDialog,
    QTextEdit, QMessageBox, QGroupBox, QFormLayout, QSlider,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QCheckBox, QDialog, QHeaderView
)
from PyQt6.QtCore import Qt, QUrl, QSizeF
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget, QGraphicsVideoItem

import app.services.ffmpeg_service as ffmpeg_service
import app.services.snapshot_service as snapshot_service
import app.services.track_metadata_service as track_service
from app.ui.advance_watermark_tab import AdvanceWatermarkTab
from app.ui.utils import (
    toggle_play_pause, get_formatted_time_str,
    handle_player_position_changed, handle_player_duration_changed,
    show_close_video_help
)
from app.ui.tracks_dialog import TracksDialog
from app.ui.components.video_player_widget import VideoPlayerWidget
from app.ui.components.track_control_widget import TrackControlWidget
from app.ui.components.snapshot_widget import SnapshotWidget
from app.ui.components.segments_widget import SegmentsWidget

class BasicCutTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.segments = []
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 3)

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

        self.track_control_widget = TrackControlWidget(self)
        left_layout.addWidget(self.track_control_widget)

        self.video_player_widget = VideoPlayerWidget(self)
        left_layout.addWidget(self.video_player_widget)

        self.snapshot_widget = SnapshotWidget(self)
        left_layout.addWidget(self.snapshot_widget)

        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 2)

        self.segments_widget = SegmentsWidget(self)
        right_layout.addWidget(self.segments_widget)

        adv_tools_group = QGroupBox("Advanced Tools")
        adv_tools_layout = QHBoxLayout()

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
        
        self.connect_signals()

    def connect_signals(self):
        self.video_player_widget.player.positionChanged.connect(self.on_player_position_changed)
        self.video_player_widget.player.durationChanged.connect(self.on_player_duration_changed)
        self.video_player_widget.slider_timeline.sliderPressed.connect(self.video_player_widget.on_slider_pressed)
        self.video_player_widget.slider_timeline.sliderReleased.connect(self.video_player_widget.on_slider_released)
        self.video_player_widget.slider_timeline.sliderMoved.connect(self.on_slider_moved)
        self.video_player_widget.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.video_player_widget.btn_set_start.clicked.connect(self.set_start_to_current)
        self.video_player_widget.btn_set_end.clicked.connect(self.set_end_to_current)
        self.video_player_widget.btn_prev_seg.clicked.connect(self.jump_to_prev_segment)
        self.video_player_widget.btn_next_seg.clicked.connect(self.jump_to_next_segment)
        self.video_player_widget.btn_help_close.clicked.connect(lambda: show_close_video_help(self))
        self.video_player_widget.btn_mute.toggled.connect(self.toggle_mute)
        self.video_player_widget.slider_volume.valueChanged.connect(self.set_volume)
        
        self.track_control_widget.btn_tracks_status.clicked.connect(self.show_tracks_dialog)
        self.track_control_widget.btn_toggle_audio.clicked.connect(self.toggle_discard_audio)
        
        self.snapshot_widget.btn_snapshot.clicked.connect(self.take_snapshot_action)
        
        self.segments_widget.table_segments.itemSelectionChanged.connect(self.on_segment_selection_changed)
        self.segments_widget.btn_export.clicked.connect(self.export_segments_action)
        self.segments_widget.cb_export_mode.currentIndexChanged.connect(self.on_export_mode_changed)
        self.segments_widget.chk_cleanup.setEnabled(False) #initially disabled

    def log(self, message: str):
        self.main_window.log(message)

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.avi *.mov *.flv);;All Files (*)"
        )
        if file_path:
            self.main_window.set_active_video(file_path)

    def set_video_path_only(self, file_path):
        self.lbl_video_path.setText(f"Selected: {os.path.basename(file_path)}\nFull Path: {file_path}")
        self.video_player_widget.player.setSource(QUrl.fromLocalFile(file_path))
        self.segments = []
        self.update_segments_table_without_save()

    def reset_tab(self):
        self.lbl_video_path.setText("No video selected. Click 'Open Video' to select one.")
        self.video_player_widget.player.setSource(QUrl())
        self.video_player_widget.slider_timeline.setRange(0, 0)
        self.video_player_widget.slider_timeline.setValue(0)
        self.video_player_widget.lbl_time.setText("00:00:00.000 / 00:00:00.000")
        self.video_player_widget.btn_play_pause.setText("Play")
        self.segments = []
        self.update_segments_table_without_save()
        self.segments_widget.txt_manual_start.clear()
        self.segments_widget.txt_manual_end.clear()

    def toggle_play_pause(self):
        toggle_play_pause(self.video_player_widget.player, self.video_player_widget.btn_play_pause)

    def on_player_position_changed(self, position):
        handle_player_position_changed(self.video_player_widget.slider_timeline, self.video_player_widget.is_slider_moving, position, self.update_time_label)

    def on_player_duration_changed(self, duration):
        handle_player_duration_changed(self.video_player_widget.slider_timeline, duration, self.update_time_label)

    def update_time_label(self):
        time_str = get_formatted_time_str(self.video_player_widget.player.position(), self.video_player_widget.player.duration())
        self.video_player_widget.lbl_time.setText(time_str)

    def on_slider_moved(self, position):
        self.video_player_widget.player.setPosition(position)
        
    def toggle_mute(self, muted):
        self.video_player_widget.audio_output.setMuted(muted)
        self.video_player_widget.btn_mute.setText("🔇" if muted else "🔈")

    def set_volume(self, volume):
        self.video_player_widget.audio_output.setVolume(volume / 100)

    def set_start_to_current(self):
        pos_sec = self.video_player_widget.player.position() / 1000.0
        time_str = ffmpeg_service.format_seconds_to_time(pos_sec)
        self.segments_widget.txt_manual_start.setText(time_str)

    def set_end_to_current(self):
        pos_sec = self.video_player_widget.player.position() / 1000.0
        time_str = ffmpeg_service.format_seconds_to_time(pos_sec)
        self.segments_widget.txt_manual_end.setText(time_str)

    def update_segments_table_without_save(self):
        self.segments_widget.table_segments.setRowCount(0)
        for i, seg in enumerate(self.segments):
            self.segments_widget.table_segments.insertRow(i)
            duration = seg["end"] - seg["start"]
            
            start_str = ffmpeg_service.format_seconds_to_time(seg["start"])
            end_str = ffmpeg_service.format_seconds_to_time(seg["end"])
            dur_str = ffmpeg_service.format_seconds_to_time(duration)
            
            self.segments_widget.table_segments.setItem(i, 0, QTableWidgetItem(f"Segment {i+1}"))
            self.segments_widget.table_segments.setItem(i, 1, QTableWidgetItem(start_str))
            self.segments_widget.table_segments.setItem(i, 2, QTableWidgetItem(end_str))
            self.segments_widget.table_segments.setItem(i, 3, QTableWidgetItem(dur_str))

    def update_segments_table(self):
        self.update_segments_table_without_save()
        if hasattr(self.main_window, "save_project_state"):
            self.main_window.save_project_state()

    def on_segment_selection_changed(self):
        selected_ranges = self.segments_widget.table_segments.selectedRanges()
        if not selected_ranges:
            self.segments_widget.selected_segment_index = -1
            return
        
        self.segments_widget.selected_segment_index = selected_ranges[0].topRow()
        if 0 <= self.segments_widget.selected_segment_index < len(self.segments):
            seg = self.segments[self.segments_widget.selected_segment_index]
            self.segments_widget.txt_manual_start.setText(ffmpeg_service.format_seconds_to_time(seg["start"]))
            self.segments_widget.txt_manual_end.setText(ffmpeg_service.format_seconds_to_time(seg["end"]))
            self.video_player_widget.player.setPosition(int(seg["start"] * 1000))

    def add_segment_action(self):
        start_str = self.segments_widget.txt_manual_start.text().strip()
        end_str = self.segments_widget.txt_manual_end.text().strip()
        
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
        if self.segments_widget.selected_segment_index < 0:
            QMessageBox.warning(self, "Warning", "Please select a segment from the table first.")
            return
            
        start_str = self.segments_widget.txt_manual_start.text().strip()
        end_str = self.segments_widget.txt_manual_end.text().strip()
        
        if not start_str or not end_str:
            QMessageBox.warning(self, "Warning", "Please specify both Start and End times.")
            return
            
        start_sec = ffmpeg_service.parse_time_to_seconds(start_str)
        end_sec = ffmpeg_service.parse_time_to_seconds(end_str)
        
        if start_sec >= end_sec:
            QMessageBox.warning(self, "Warning", "Start time must be less than End time.")
            return
            
        self.segments[self.segments_widget.selected_segment_index] = {"start": start_sec, "end": end_sec}
        self.segments.sort(key=lambda s: s["start"])
        self.update_segments_table()
        self.log(f"Updated segment to: {start_str} - {end_str}")

    def delete_segment_action(self):
        if self.segments_widget.selected_segment_index < 0:
            QMessageBox.warning(self, "Warning", "Please select a segment from the table first.")
            return
            
        deleted = self.segments.pop(self.segments_widget.selected_segment_index)
        self.update_segments_table()
        self.log(f"Deleted segment: {ffmpeg_service.format_seconds_to_time(deleted['start'])} - {ffmpeg_service.format_seconds_to_time(deleted['end'])}")

    def jump_to_prev_segment(self):
        if not self.segments:
            return
        
        current_pos_sec = self.video_player_widget.player.position() / 1000.0
        target_seg = None
        for seg in reversed(self.segments):
            if seg["start"] < current_pos_sec - 0.5:
                target_seg = seg
                break
        
        if target_seg is None:
            target_seg = self.segments[-1]
            
        self.video_player_widget.player.setPosition(int(target_seg["start"] * 1000))
        self.log(f"Jumped to segment start: {ffmpeg_service.format_seconds_to_time(target_seg['start'])}")

    def jump_to_next_segment(self):
        if not self.segments:
            return
            
        current_pos_sec = self.video_player_widget.player.position() / 1000.0
        target_seg = None
        for seg in self.segments:
            if seg["start"] > current_pos_sec + 0.5:
                target_seg = seg
                break
                
        if target_seg is None:
            target_seg = self.segments[0]
            
        self.video_player_widget.player.setPosition(int(target_seg["start"] * 1000))
        self.log(f"Jumped to segment start: {ffmpeg_service.format_seconds_to_time(target_seg['start'])}")

    def on_export_mode_changed(self, index):
        mode = self.segments_widget.cb_export_mode.currentData()
        self.segments_widget.chk_cleanup.setEnabled(mode == "merge")

    def export_segments_action(self):
        if not self.main_window.selected_video_path:
            QMessageBox.warning(self, "Warning", "Please select an input video first!")
            return
            
        if not self.segments:
            QMessageBox.warning(self, "Warning", "No segments defined to export.")
            return

        dest_dir = QFileDialog.getExistingDirectory(
            self, "Select Directory to Save Exported Files", os.path.dirname(self.main_window.selected_video_path)
        )
        if not dest_dir:
            return

        export_mode = self.segments_widget.cb_export_mode.currentData()
        do_cleanup = self.segments_widget.chk_cleanup.isChecked() and export_mode == 'merge'

        self.log(f"Starting export with mode: {export_mode}")
        
        video_name = os.path.basename(self.main_window.selected_video_path)
        base_name, ext = os.path.splitext(video_name)
        
        exported_files = []
        success_count = 0
        has_error = False

        for i, seg in enumerate(self.segments):
            start_str = ffmpeg_service.format_seconds_to_time(seg["start"], include_ms=False)
            end_str = ffmpeg_service.format_seconds_to_time(seg["end"], include_ms=False)
            
            safe_start = start_str.replace(":", "-")
            safe_end = end_str.replace(":", "-")
            
            output_filename = f"{base_name}_{safe_start}_{safe_end}{ext}"
            output_path = os.path.join(dest_dir, output_filename)
            
            self.log(f"Exporting Segment {i+1}: {start_str} to {end_str} -> {output_filename}")
            
            try:
                ffmpeg_service.cut_video(self.main_window.selected_video_path, output_path, start_str, end_str, audio_codec="copy" if not self.track_control_widget.is_audio_discarded else None)
                success_count += 1
                exported_files.append(output_path)
                self.log(f"Exported: {output_filename}")
            except Exception as e:
                has_error = True
                self.log(f"Error exporting Segment {i+1}: {str(e)}")

        if has_error:
            QMessageBox.warning(self, "Export Error", f"Exported {success_count}/{len(self.segments)} segments. Check logs for details.")
            return

        if export_mode == 'merge':
            merged_filename = f"{base_name}_merged{ext}"
            merged_output_path = os.path.join(dest_dir, merged_filename)
            
            self.log(f"Merging {len(exported_files)} files into {merged_filename}...")
            try:
                ffmpeg_service.merge_videos(exported_files, merged_output_path)
                self.log(f"Successfully merged files into {merged_filename}")

                if do_cleanup:
                    self.log("Cleaning up intermediate segment files...")
                    cleaned_count = 0
                    for f_path in exported_files:
                        try:
                            os.remove(f_path)
                            cleaned_count += 1
                        except OSError as e:
                            self.log(f"Error deleting file {f_path}: {e}")
                    self.log(f"Cleaned up {cleaned_count} files.")
                
                QMessageBox.information(self, "Export & Merge Finished", f"Successfully exported {success_count} segments and merged them into {merged_filename}")

            except Exception as e:
                self.log(f"Error merging files: {str(e)}")
                QMessageBox.critical(self, "Merge Error", f"Failed to merge files. Your separate segment files are still available.\nError: {str(e)}")
        else:
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

    def load_metadata(self):
        if not self.main_window.selected_video_path:
            self.track_control_widget.tracks = []
            self.update_tracks_button()
            return
        try:
            self.log("Loading video streams...")
            self.track_control_widget.tracks = track_service.get_streams(self.main_window.selected_video_path)
            self.update_tracks_button()
            self.log(f"Found {len(self.track_control_widget.tracks)} streams.")
        except Exception as e:
            self.log(f"Error loading streams: {e}")
            self.track_control_widget.tracks = []
            self.update_tracks_button()

    def update_tracks_button(self):
        total_tracks = len(self.track_control_widget.tracks)
        if self.track_control_widget.is_audio_discarded:
            enabled_tracks = sum(1 for t in self.track_control_widget.tracks if t.get("codec_type") == "video")
        else:
            enabled_tracks = total_tracks

        self.track_control_widget.btn_tracks_status.setText(f"Tracks ({enabled_tracks}/{total_tracks})")

    def show_tracks_dialog(self):
        if not self.track_control_widget.tracks:
            QMessageBox.information(self, "Info", "No tracks loaded. Please open a video.")
            return
        dialog = TracksDialog(self.track_control_widget.tracks, self)
        if dialog.exec():
            self.update_tracks_button()
    
    def toggle_discard_audio(self):
        self.track_control_widget.is_audio_discarded = not self.track_control_widget.is_audio_discarded
        if self.track_control_widget.is_audio_discarded:
            self.track_control_widget.btn_toggle_audio.setText("Discard audio")
        else:
            self.track_control_widget.btn_toggle_audio.setText("Keep audio")
        self.update_tracks_button()

    def take_snapshot_action(self):
        if not self.main_window.selected_video_path:
            QMessageBox.warning(self, "Warning", "Please open a video first.")
            return

        video_player = self.video_player_widget.player
        timestamp_sec = video_player.position() / 1000.0
        
        file_format = self.snapshot_widget.cb_snapshot_format.currentData()
        pattern = self.snapshot_widget.txt_snapshot_pattern.text()
        use_png = (file_format == "png")

        base_name, _ = os.path.splitext(os.path.basename(self.main_window.selected_video_path))
        ts_formatted = ffmpeg_service.format_seconds_to_time(timestamp_sec, include_ms=True).replace(":", "-").replace(".", "-")

        filename = pattern.replace("[filename]", base_name)\
                            .replace("[timestamp]", ts_formatted)\
                            .replace("[ext]", file_format)

        output_dir = os.path.dirname(self.main_window.selected_video_path)
        output_path = os.path.join(output_dir, filename)

        try:
            self.log(f"Taking snapshot: {filename} at {timestamp_sec:.3f}s")
            snapshot_service.take_snapshot(
                self.main_window.selected_video_path,
                output_path,
                timestamp_sec,
                quality=90, 
                use_png=use_png
            )
            self.log(f"Successfully saved snapshot to {output_path}")
            QMessageBox.information(self, "Success", f"Snapshot saved to:\n{output_path}")
        except Exception as e:
            self.log(f"Error taking snapshot: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to take snapshot:\n{str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_video_path = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Mini LosslessCut - Professional Edition with AI")
        self.resize(1200, 850)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.basic_tab = BasicCutTab(self)
        self.advance_tab = AdvanceWatermarkTab(self)
        
        self.advance_tab.log_message.connect(self.log)

        self.tabs.addTab(self.basic_tab, "Basic Cut / Main")
        self.tabs.addTab(self.advance_tab, "Advance Watermark & AI")
        main_layout.addWidget(self.tabs, 1)

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
        self.basic_tab.set_video_path_only(video_path)
        self.advance_tab.set_video_path_only(video_path)
        self.basic_tab.load_metadata()
        # self.load_project_state(video_path)

    def close_video(self):
        self.reset_workspace()

    def reset_workspace(self):
        from app.core.config_manager import reset_workspace
        reset_workspace(self)
        self.log("Workspace reset. Closing player and clearing state.")

    def save_project_state(self):
        from app.core.config_manager import save_project_state
        save_project_state(self)

    def load_project_state(self, video_path):
        from app.core.config_manager import load_project_state
        load_project_state(self, video_path)

    def log(self, message: str):
        self.log_output.append(message)

    def keyPressEvent(self, event):
        is_ctrl_w = (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_W
        is_cmd_w = (event.modifiers() & Qt.KeyboardModifier.MetaModifier) and event.key() == Qt.Key.Key_W
        if is_ctrl_w or is_cmd_w:
            self.close_video()
            return

        if self.tabs.currentWidget() == self.basic_tab:
            if event.key() == Qt.Key.Key_BracketLeft:
                self.basic_tab.set_start_to_current()
            elif event.key() == Qt.Key.Key_BracketRight:
                self.basic_tab.set_end_to_current()
            elif event.key() == Qt.Key.Key_Space:
                focused = self.focusWidget()
                if not isinstance(focused, QLineEdit):
                    self.basic_tab.toggle_play_pause()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_video_path = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Mini LosslessCut - Professional Edition with AI")
        self.resize(1200, 850)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.basic_tab = BasicCutTab(self)
        self.advance_tab = AdvanceWatermarkTab(self)
        
        self.advance_tab.log_message.connect(self.log)

        self.tabs.addTab(self.basic_tab, "Basic Cut / Main")
        self.tabs.addTab(self.advance_tab, "Advance Watermark & AI")
        main_layout.addWidget(self.tabs, 1)

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
        self.basic_tab.set_video_path_only(video_path)
        self.advance_tab.set_video_path_only(video_path)
        self.basic_tab.load_metadata()
        self.load_project_state(video_path)

    def close_video(self):
        self.reset_workspace()

    def reset_workspace(self):
        from app.core.config_manager import reset_workspace
        reset_workspace(self)
        self.log("Workspace reset. Closing player and clearing state.")

    def save_project_state(self):
        from app.core.config_manager import save_project_state
        save_project_state(self)

    def load_project_state(self, video_path):
        from app.core.config_manager import load_project_state
        load_project_state(self, video_path)

    def log(self, message: str):
        self.log_output.append(message)

    def keyPressEvent(self, event):
        is_ctrl_w = (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_W
        is_cmd_w = (event.modifiers() & Qt.KeyboardModifier.MetaModifier) and event.key() == Qt.Key.Key_W
        if is_ctrl_w or is_cmd_w:
            self.close_video()
            return

        if self.tabs.currentWidget() == self.basic_tab:
            if event.key() == Qt.Key.Key_BracketLeft:
                self.basic_tab.set_start_to_current()
            elif event.key() == Qt.Key.Key_BracketRight:
                self.basic_tab.set_end_to_current()
            elif event.key() == Qt.Key.Key_Space:
                focused = self.focusWidget()
                if not isinstance(focused, QLineEdit):
                    self.basic_tab.toggle_play_pause()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
