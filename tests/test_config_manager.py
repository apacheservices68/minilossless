import os
import json
import pytest
from unittest.mock import MagicMock

from app.core.config_manager import (
    save_project_state,
    load_project_state,
    reset_workspace,
)

class MockMainWindow:
    def __init__(self):
        self.selected_video_path = None
        self.log = MagicMock()
        self.reset_workspace = MagicMock()
        
        # Basic Tab Mock
        self.basic_tab = MagicMock()
        self.basic_tab.segments = [
            {"start": 0.0, "end": 10.0},
            {"start": 15.5, "end": 20.0}
        ]
        self.basic_tab.player = MagicMock()
        self.basic_tab.list_widget = MagicMock()
        self.basic_tab.update_segments_table_without_save = MagicMock()
        
        # Advance Tab Mock
        self.advance_tab = MagicMock()
        self.advance_tab.chk_cuda = MagicMock()
        self.advance_tab.chk_cuda.isChecked.return_value = True
        
        # Face Blur Mocks
        self.advance_tab.chk_face_blur = MagicMock()
        self.advance_tab.chk_face_blur.isChecked.return_value = False
        
        self.advance_tab.cb_face_blur_type = MagicMock()
        self.advance_tab.cb_face_blur_type.currentData.return_value = "Square"
        self.advance_tab.cb_face_blur_type.findData.return_value = 0  # Trả về int thay vì MagicMock
        
        self.advance_tab.cb_face_blur_style = MagicMock()
        self.advance_tab.cb_face_blur_style.currentData.return_value = "Gaussian"
        self.advance_tab.cb_face_blur_style.findData.return_value = 0  # Trả về int thay vì MagicMock
        
        self.advance_tab.spin_face_blur_strength = MagicMock()
        self.advance_tab.spin_face_blur_strength.value.return_value = 10
        self.advance_tab.spin_face_blur_pct = MagicMock()
        self.advance_tab.spin_face_blur_pct.value.return_value = 15
        
        # Background Blur Mocks
        self.advance_tab.chk_bg_blur = MagicMock()
        self.advance_tab.chk_bg_blur.isChecked.return_value = True
        self.advance_tab.spin_bg_strength = MagicMock()
        self.advance_tab.spin_bg_strength.value.return_value = 85
        
        # Overlays & Scene Mocks
        self.advance_tab.text_items = []
        self.advance_tab.scene = MagicMock()
        self.advance_tab.list_overlays = MagicMock()
        self.advance_tab.app_font_family = "Arial"


def test_reset_workspace():
    """
    Test reset_workspace clears video path.
    """
    mw = MockMainWindow()
    reset_workspace(mw)
    
    assert mw.selected_video_path == ""


def test_save_load_project_state(tmp_path, mocker):
    """
    Test save_project_state and load_project_state using tmp_path directory.
    """
    mw = MockMainWindow()
    
    # Path inside pytest tmp_path
    video_file = tmp_path / "test_video.mp4"
    video_file.touch()
    video_path = str(video_file)
    
    mw.selected_video_path = video_path
    
    # Mock Text Overlays
    mock_item = MagicMock()
    mock_item.toPlainText.return_value = "Logo Text"
    mock_item.font_size = 24
    mock_item.pos.return_value.x.return_value = 100.0
    mock_item.pos.return_value.y.return_value = 150.0
    mock_item.angle = 45.0
    mock_item.opacity_val = 0.8
    mw.advance_tab.text_items = [mock_item]
    
    # Save State
    save_project_state(mw)
    
    json_path = str(tmp_path / "test_video.json")
    assert os.path.exists(json_path)
    
    # Verify JSON Content
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["video_path"] == video_path
    assert data["hardware_acceleration"] is True
    assert data["bg_blur"]["enabled"] is True
    assert data["bg_blur"]["amount"] == 85
    assert len(data["watermarks"]["advance_overlays"]) == 1
    assert data["watermarks"]["advance_overlays"][0]["text"] == "Logo Text"

    # Reset mocks to test load_project_state
    mw.advance_tab.chk_cuda.setChecked.reset_mock()
    mw.advance_tab.chk_bg_blur.setChecked.reset_mock()
    mw.advance_tab.spin_bg_strength.setValue.reset_mock()

    # Patch DraggableTextItem & QListWidgetItem để không đụng vào Qt C++ GUI thật gây crash
    mocker.patch("app.ui.advance_watermark_tab.DraggableTextItem")
    mocker.patch("PyQt6.QtWidgets.QListWidgetItem")

    # Run load_project_state
    load_project_state(mw, video_path)

    # Verify load_project_state applied settings back to UI
    mw.advance_tab.chk_cuda.setChecked.assert_called_with(True)
    mw.advance_tab.chk_bg_blur.setChecked.assert_called_with(True)
    mw.advance_tab.spin_bg_strength.setValue.assert_called_with(85)