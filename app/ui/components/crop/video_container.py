from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout
from PyQt6.QtCore import QSize, Qt

class VideoContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_widget = None
        self.aspect_ratio = 16 / 9.0
        self.h_ruler = None
        self.v_ruler = None
        self.PREVIEW_DEFAULT = 720
        self.PREVIEW_MAX_W = 1280
        self.PREVIEW_MAX_H = 720
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

    def set_h_ruler(self, ruler):
        self.h_ruler = ruler

    def set_v_ruler(self, ruler):
        self.v_ruler = ruler

    def set_video_widget(self, widget):
        if self.video_widget:
            self.layout().removeWidget(self.video_widget)
            self.video_widget.setParent(None)

        self.video_widget = widget
        self.layout().addWidget(self.video_widget)
        
        # Bắt buộc giữ tỷ lệ chuẩn gốc (Chống méo mặt)
        self._apply_keep_aspect_ratio(self.video_widget)
        self._update_player_layout()

    def _apply_keep_aspect_ratio(self, target_widget):
        if hasattr(target_widget, 'setAspectRatioMode'):
            target_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        elif hasattr(target_widget, 'children'):
            for child in target_widget.children():
                self._apply_keep_aspect_ratio(child)

    def set_aspect_ratio(self, ratio):
        self.aspect_ratio = ratio if ratio > 0 else 1.0
        
        # TỰ ĐỘNG TÍNH TOÁN THEO CHIỀU DÀI HƠN
        # Nếu là video ngang (Ratio >= 1): Ép Max Width = 800px
        # Nếu là video dọc (Ratio < 1):  Ép Max Height = 800px
        # if self.aspect_ratio >= 1.0:
        #     self.PREVIEW_MAX_W = 800
        #     self.PREVIEW_MAX_H = int(800 / self.aspect_ratio)
        # else:
        #     self.PREVIEW_MAX_H = 800
        #     self.PREVIEW_MAX_W = int(800 * self.aspect_ratio)
            
        self._update_player_layout()

    def _update_player_layout(self):
        if not self.video_widget:
            return

        # 1. Tính toán kích thước hiển thị THỰC TẾ
        target_w = self.PREVIEW_MAX_W
        target_h = int(target_w / self.aspect_ratio)

        # Nếu là video dọc (9:16)
        if target_h > self.PREVIEW_MAX_H:
            target_h = self.PREVIEW_MAX_H
            target_w = int(target_h * self.aspect_ratio)

        # 2. CHÌA KHÓA DIỆT VIỀN ĐEN: Ép cả Stack Container lẫn Child Widget 
        self.video_widget.setFixedSize(target_w, target_h)
        if hasattr(self.video_widget, 'children'):
            for child in self.video_widget.children():
                if hasattr(child, 'setFixedSize'):
                    child.setFixedSize(target_w, target_h)

        self.setFixedSize(target_w, target_h)

        # 3. Đồng bộ chuẩn 100% độ dài 2 thước Ruler
        if self.h_ruler:
            self.h_ruler.setFixedWidth(target_w)
        if self.v_ruler:
            self.v_ruler.setFixedHeight(target_h)

        # Tìm chính xác class CropVideoTab ở cấp cha
        parent_tab = self.parent()
        while parent_tab and not hasattr(parent_tab, 'player_controls'):
            parent_tab = parent_tab.parent()

        if parent_tab and hasattr(parent_tab, 'player_controls'):
            parent_tab.player_controls.setFixedWidth(target_w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_player_layout()

    def minimumSizeHint(self):
        return QSize(0, 0)

    def sizeHint(self):
        return QSize(self.PREVIEW_MAX_W, self.PREVIEW_MAX_H)