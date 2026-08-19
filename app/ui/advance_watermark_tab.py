from datetime import datetime
import os
import cv2
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog
from PyQt6.QtCore import pyqtSignal, QUrl
from PyQt6.QtGui import QFontDatabase

from app.services.ai_process_worker import AIProcessWorker
from app.ui.components.video_player_preview_widget import VideoPlayerPreviewWidget, DraggableTextItem
from app.ui.components.text_overlay_editor_widget import TextOverlayEditorWidget
from app.ui.components.ai_filters_widget import AIFiltersWidget
from app.ui.components.export_pipeline_widget import ExportPipelineWidget
from app.core.helpers import check_cuda_support, calculate_relative_text_overlays
from app.core.watermark_constants import (
    DEFAULT_FONT_PATH, DEFAULT_FONT_FAMILY, 
    DEFAULT_VIDEO_WIDTH, DEFAULT_VIDEO_HEIGHT
)

class AdvanceWatermarkTab(QWidget):
    log_message = pyqtSignal(str)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left Panel
        self.video_player_widget = VideoPlayerPreviewWidget(self)
        main_layout.addWidget(self.video_player_widget, 3)
        
        # Right Panel
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 2)
        
        self.text_editor_widget = TextOverlayEditorWidget(self)
        right_layout.addWidget(self.text_editor_widget)
        
        self.ai_filters_widget = AIFiltersWidget(self)
        right_layout.addWidget(self.ai_filters_widget)
        
        self.export_widget = ExportPipelineWidget(self)
        right_layout.addWidget(self.export_widget)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        font_id = QFontDatabase.addApplicationFont(DEFAULT_FONT_PATH)
        if font_id != -1:
            self.app_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            self.app_font_family = DEFAULT_FONT_FAMILY
            
        self.selected_video_path = ""
        self.text_items = []
        self.selected_item = None
        
        self.init_ui()
        self.connect_signals()

    def trigger_auto_save(self):
        main_win = self.window()
        if hasattr(main_win, "save_project_state"):
            main_win.save_project_state()
            current_time = datetime.now().strftime("%H:%M:%S")
            self.log_message.emit(f"[{current_time}]Project state auto-saved.")

    def connect_signals(self):
        self.video_player_widget.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.text_editor_widget.add_text_overlay.connect(self.add_new_text_overlay)
        self.text_editor_widget.delete_selected_text.connect(self.delete_selected_text)
        self.text_editor_widget.selection_changed.connect(self.on_list_selection_changed)
        self.text_editor_widget.properties_changed.connect(self.on_control_properties_changed)
        self.ai_filters_widget.cuda_state_changed.connect(self.on_check_cuda_support)
        self.ai_filters_widget.state_changed.connect(self.trigger_auto_save)
        self.export_widget.start_export.connect(self.start_ai_processing)

    def on_check_cuda_support(self, is_checked):
        if is_checked and not check_cuda_support():
            QMessageBox.warning(
                self, "CUDA Not Available",
                "NVIDIA GPU with CUDA support was not detected on your system. Reverting to CPU mode."
            )
            self.ai_filters_widget.chk_cuda.setChecked(False)

    def reset_tab(self):
        self.selected_video_path = ""
        self.video_player_widget.reset_video()
        
        for item in self.text_items:
            try:
                self.video_player_widget.scene.removeItem(item)
            except Exception:
                pass
        self.text_items.clear()
        self.text_editor_widget.clear_overlays()
        self.selected_item = None

    def set_video_path_only(self, path):
        self.selected_video_path = path
        self.video_player_widget.set_video(path)

        for item in self.text_items:
            try:
                self.video_player_widget.scene.removeItem(item)
            except Exception:
                pass
        self.text_items.clear()
        self.text_editor_widget.clear_overlays()
        self.selected_item = None

    def add_new_text_overlay(self):
        text_val = f"Text {len(self.text_items) + 1}"
        item = DraggableTextItem(text=text_val, font_size=32, angle=0.0, opacity=1.0, font_family=self.app_font_family)
        
        item.setZValue(100 + len(self.text_items))
        item.setPos(50 + len(self.text_items) * 15, 50 + len(self.text_items) * 15)
        
        self.video_player_widget.scene.addItem(item)
        self.text_items.append(item)
        
        self.text_editor_widget.add_overlay_item(text_val)
        self.text_editor_widget.set_selected_row(len(self.text_items) - 1)
        item.setSelected(True)
        self.log_message.emit(f"Added text overlay: \'{text_val}\'")
        self.trigger_auto_save()

    def delete_selected_text(self):
        # Ưu tiên lấy item từ dòng đang chọn ở list_widget
        current_row = -1
        if hasattr(self.text_editor_widget, "list_widget"):
            current_row = self.text_editor_widget.list_widget.currentRow()

        target_item = None
        if 0 <= current_row < len(self.text_items):
            target_item = self.text_items[current_row]
        elif self.selected_item in self.text_items:
            target_item = self.selected_item

        if not target_item or target_item not in self.text_items:
            QMessageBox.warning(self, "Warning", "Please select a text overlay to delete first.")
            return

        idx = self.text_items.index(target_item)
        
        # Xóa khỏi danh sách & UI list
        self.text_items.pop(idx)
        self.text_editor_widget.take_item(idx)

        # Xóa khỏi QGraphicsScene
        try:
            self.video_player_widget.scene.removeItem(target_item)
        except Exception:
            pass

        self.selected_item = None
        self.log_message.emit("Deleted selected text overlay.")
        self.trigger_auto_save()

    def on_scene_selection_changed(self):
        selected = self.video_player_widget.scene.selectedItems()
        text_selected = [i for i in selected if isinstance(i, DraggableTextItem)]

        if text_selected:
            item = text_selected[0]
            self.selected_item = item

            self.text_editor_widget.set_properties(
                item.toPlainText(), item.font_size, item.angle, item.opacity_val
            )

            if item in self.text_items:
                idx = self.text_items.index(item)
                # Chặn bẫy loop signal khi đồng bộ lại dòng chọn
                self.text_editor_widget.blockSignals(True)
                self.text_editor_widget.set_selected_row(idx)
                self.text_editor_widget.blockSignals(False)

    def on_list_selection_changed(self, row):
        if 0 <= row < len(self.text_items):
            item = self.text_items[row]
            self.selected_item = item

            # Chặn signal của Scene để tránh trigger ngược làm đè selected_item
            self.video_player_widget.scene.blockSignals(True)
            self.video_player_widget.scene.clearSelection()
            item.setSelected(True)
            self.video_player_widget.scene.blockSignals(False)

            self.text_editor_widget.set_properties(
                item.toPlainText(), item.font_size, item.angle, item.opacity_val
            )

    def on_control_properties_changed(self):
        if self.selected_item:
            props = self.text_editor_widget.get_properties()
            self.selected_item.update_style(**props)
            
            idx = self.text_items.index(self.selected_item)
            self.text_editor_widget.item(idx).setText(props["text"])
            
            self.trigger_auto_save()

    def start_ai_processing(self):
        if not self.selected_video_path:
            QMessageBox.warning(self, "Warning", "Please load a video from the main interface first.")
            return
            
        cap = cv2.VideoCapture(self.selected_video_path)
        if not cap.isOpened():
            QMessageBox.critical(self, "Error", "Cannot open loaded video.")
            return
        video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        texts_to_backend = calculate_relative_text_overlays(self.text_items, self.video_player_widget.video_item)

        ext = os.path.splitext(self.selected_video_path)[1]
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save AI Exported Video As", f"ai_output{ext}", f"Video Files (*{ext});;All Files (*)"
        )
        if not output_path:
            return

        ai_state = self.ai_filters_widget.get_state()

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("Confirm AI Export Configuration")
        msg_box.setText("Are you sure you want to export the video with selected configurations?")
        
        cuda_status = "Enabled" if ai_state["cuda"] else "Disabled"
        face_type_str = self.ai_filters_widget.cb_face_blur_type.currentText()
        if ai_state["face_blur_type"] == "Image":
            face_type_str += f" ({os.path.basename(ai_state['face_blur_image_path'])})"
        face_style_str = self.ai_filters_widget.cb_face_blur_style.currentText()
        face_strength = ai_state["face_blur_strength"]
        fblur_status = f"Enabled ({face_type_str}, style {face_style_str}, strength {face_strength}, top {ai_state['face_blur_pct']}% of face)" if ai_state['face_blur'] else "Disabled"
        bblur_status = f"Enabled (kernel {ai_state['bg_blur_strength']}px)" if ai_state["bg_blur"] else "Disabled"
        
        details = f"""
Input: {os.path.basename(self.selected_video_path)}
Output: {os.path.basename(output_path)}
Resolution: {video_w}x{video_h}

- CUDA Hardware Acceleration: {cuda_status}
- Face Blur (Face detector): {fblur_status}
- Background Blur (Selfie segmenter): {bblur_status}
- Interactive text overlays: {len(texts_to_backend)} text(s) definition mapped
"""
        msg_box.setInformativeText(details)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        res = msg_box.exec()
        if res == QMessageBox.StandardButton.No:
            self.log_message.emit("Export canceled by user.")
            return
            
        self.export_widget.set_processing_state(True)
        self.log_message.emit("Starting AI processing thread...")
        
        self.worker = AIProcessWorker(
            input_path=self.selected_video_path,
            output_path=output_path,
            texts=texts_to_backend,
            use_cuda=ai_state["cuda"],
            face_blur=ai_state["face_blur"],
            face_blur_pct=ai_state["face_blur_pct"],
            face_blur_type=ai_state["face_blur_type"],
            face_blur_image_path=ai_state["face_blur_image_path"] if ai_state["face_blur_type"] == "Image" else None,
            face_blur_style=ai_state["face_blur_style"],
            face_blur_strength=ai_state["face_blur_strength"],
            bg_blur=ai_state["bg_blur"],
            bg_blur_strength=ai_state["bg_blur_strength"]
        )
        
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_progress(self, percent, text):
        self.export_widget.set_progress(percent, text)

    def on_worker_finished(self, success, msg):
        self.export_widget.set_processing_state(False)
        if success:
            self.export_widget.set_progress(100, "Finished Successfully!")
            self.log_message.emit("AI Processing thread completed successfully.")
            QMessageBox.information(self, "Success", "Video processed and exported successfully!")
        else:
            self.export_widget.set_progress(0, "Error during process!")
            self.log_message.emit(f"AI Process Error: {msg}")
            QMessageBox.critical(self, "Error", f"An error occurred during video processing:\n{msg}")

    def get_state(self):
        text_states = []
        for item in self.text_items:
            # Lấy vị trí thực tế của item trên QGraphicsScene
            # pos = item.scenePos()
            pos = item.pos() # Sử dụng .pos() để lấy vị trí tương đối trong QGraphicsScene
            
            text_states.append({
                'text': item.toPlainText(),
                'font_size': item.font_size,
                'angle': item.angle,
                'opacity': item.opacity_val,
                'pos_x': float(pos.x()),  # Gọi hàm .x() từ QPointF
                'pos_y': float(pos.y()),  # Gọi hàm .y() từ QPointF
            })
        
        state = {
            'video_path': self.selected_video_path,
            'texts': text_states,
            'ai_filters': self.ai_filters_widget.get_state(),
        }
        return state

    def set_state(self, state):
        # 1. Kiểm tra an toàn dữ liệu đầu vào
        if not state or not isinstance(state, dict):
            return

        # 2. Khôi phục Video Path bằng đúng tên hàm trong file (set_video_path_only)
        video_path = state.get("video_path")
        if video_path and os.path.exists(video_path):
            self.set_video_path_only(video_path)

        # 3. Xóa các text item cũ đang hiển thị trên QGraphicsScene
        for item in self.text_items:
            try:
                self.video_player_widget.scene.removeItem(item)
            except Exception:
                pass
        self.text_items.clear()
        self.text_editor_widget.clear_overlays()

        # 4. Nạp danh sách Text Overlays từ state
        text_states = state.get("texts", [])
        for t_state in text_states:
            if not isinstance(t_state, dict):
                continue

            item = DraggableTextItem(
                text=t_state.get("text", "Text"),
                font_size=t_state.get("font_size", 32),
                angle=t_state.get("angle", 0.0),
                opacity=t_state.get("opacity", 1.0),
                font_family=self.app_font_family
            )

            item.setPos(t_state.get("pos_x", 50.0), t_state.get("pos_y", 50.0))
            item.setZValue(100 + len(self.text_items))
            
            self.video_player_widget.scene.addItem(item)
            self.text_items.append(item)
            self.text_editor_widget.add_overlay_item(t_state.get("text", "Text"))

        # Chọn item đầu tiên nếu có
        if self.text_items:
            self.text_editor_widget.set_selected_row(0)
            self.text_items[0].setSelected(True)
            self.on_scene_selection_changed()

        # 5. Chuyển cấu hình AI Filters (CUDA, Face Blur, BG Blur) xuống AIFiltersWidget
        if state.get("ai_filters"):
            self.ai_filters_widget.set_state(state["ai_filters"])

    # Add on 08172026 @apacheservice68 | editor encapsulating all reset actions
    def reset_tab(self):
        self.selected_video_path = ""
        self.text_items.clear()
        self.selected_item = None
        
        # Gọi hàm reset của từng widget con
        self.video_player_widget.reset_video()
        self.text_editor_widget.reset_ui()
        self.ai_filters_widget.reset_ui()