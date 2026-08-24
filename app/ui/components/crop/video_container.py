from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import QRect, QSize, Qt

from .crop_overlay_widget import CropOverlayWidget

class VideoContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_widget = None
        self.overlay_widget = None
        self.aspect_ratio = 16 / 9.0
        self.h_ruler = None
        self.v_ruler = None
        self.PREVIEW_DEFAULT = 720
        self.PREVIEW_MAX_W = 1280
        self.PREVIEW_MAX_H = 720
        self.setContentsMargins(0, 0, 0, 0)

    def set_h_ruler(self, ruler):
        self.h_ruler = ruler

    def set_v_ruler(self, ruler):
        self.v_ruler = ruler

    def set_video_widget(self, video_widget, overlay_widget):
        if self.video_widget:
            self.video_widget.setParent(None)
        if self.overlay_widget:
            self.overlay_widget.setParent(None)

        self.video_widget = video_widget
        self.overlay_widget = overlay_widget

        self.video_widget.setParent(self)
        self.overlay_widget.setParent(self)

        # Bật cờ nền trong suốt bắt buộc của PyQt6 để vẽ đè lên video
        self.overlay_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.overlay_widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Bắt buộc giữ tỷ lệ chuẩn gốc (Chống méo mặt)
        self._apply_keep_aspect_ratio(self.video_widget)
        self._update_player_layout()
        
        self.overlay_widget.raise_()

    def _apply_keep_aspect_ratio(self, target_widget):
        if hasattr(target_widget, 'setAspectRatioMode'):
            target_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        elif hasattr(target_widget, 'children'):
            for child in target_widget.children():
                self._apply_keep_aspect_ratio(child)

    def set_aspect_ratio(self, ratio):
        self.aspect_ratio = ratio if ratio > 0 else 1.0
        self._update_player_layout()

    def _update_player_layout(self):
        if not self.video_widget:
            return

        # 1. Calculate the REAL display size
        target_w = self.PREVIEW_MAX_W
        target_h = int(target_w / self.aspect_ratio)

        # If it's a vertical video (9:16)
        if target_h > self.PREVIEW_MAX_H:
            target_h = self.PREVIEW_MAX_H
            target_w = int(target_h * self.aspect_ratio)

        # 2. Key to eliminating black borders: Force both container and child widget sizes
        self.video_widget.setGeometry(0, 0, target_w, target_h)
        
        # Nếu video_widget là QGraphicsView, bắt buộc ép fitInView lại để video phóng to vừa vặn
        if hasattr(self.video_widget, 'parent') and self.video_widget.parent():
            player_widget = self.video_widget.parent()
            if hasattr(player_widget, 'fit_in_view'):
                player_widget.fit_in_view()

        if self.overlay_widget:
            self.overlay_widget.setGeometry(0, 0, target_w, target_h)
            self.overlay_widget.raise_()  # Ép overlay luôn nằm trên cùng Z-order
            self.overlay_widget.update()  # Kích hoạt vẽ lại paintEvent

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

    def reset_ui(self):
        """Reset kích thước VideoContainer và clear Overlay"""
        self.aspect_ratio = 16 / 9.0
        
        # Reset kích thước container về mặc định
        self.setFixedSize(self.PREVIEW_MAX_W, self.PREVIEW_MAX_H)
        
        # Reset 2 ruler nếu có
        if self.h_ruler:
            self.h_ruler.setFixedWidth(self.PREVIEW_MAX_W)
        if self.v_ruler:
            self.v_ruler.setFixedHeight(self.PREVIEW_MAX_H)

        # Reset overlay vẽ đè
        if self.overlay_widget:
            self.overlay_widget.set_video_resolution(0, 0)
            self.overlay_widget.set_crop_rect(QRect(0, 0, 0, 0))
            self.overlay_widget.update()