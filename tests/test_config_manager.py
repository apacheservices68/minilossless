import os
import json
import pytest
from unittest.mock import MagicMock
from PyQt6.QtCore import QUrl, QSizeF
from app.core.config_manager import save_project_state, load_project_state, reset_workspace

class MockBasicTab:
    def __init__(self):
        self.player = MagicMock()
        self.selected_video_path = ""
        self.lbl_video_path = MagicMock()
        self.slider_timeline = MagicMock()
        self.lbl_time = MagicMock()
        self.btn_play_pause = MagicMock()
        self.segments = []
        self.txt_manual_start = MagicMock()
        self.txt_manual_end = MagicMock()
        self.txt_watermark = MagicMock()
        self.cb_position = MagicMock()
        
    def update_segments_table_without_save(self):
        pass

class MockAdvanceTab:
    def __init__(self):
        self.player = MagicMock()
        self.selected_video_path = ""
        self.slider_timeline = MagicMock()
        self.lbl_time = MagicMock()
        self.btn_play_pause = MagicMock()
        self.scene = MagicMock()
        self.video_item = MagicMock()
        self.video_w = 1280
        self.video_h = 720
        self.text_items = []
        self.list_overlays = MagicMock()
        self.selected_item = None
        self.txt_overlay_text = MagicMock()
        self.txt_face_image_path = MagicMock()
        self.chk_cuda = MagicMock()
        self.chk_face_blur = MagicMock()
        self.chk_bg_blur = MagicMock()
        self.spin_font_size = MagicMock()
        self.slider_rotation = MagicMock()
        self.slider_opacity = MagicMock()
        self.spin_face_blur_pct = MagicMock()
        self.spin_face_blur_strength = MagicMock()
        self.spin_bg_strength = MagicMock()
        self.cb_face_blur_type = MagicMock()
        self.cb_face_blur_style = MagicMock()
        self.widget_face_image = MagicMock()
        self.app_font_family = "DejaVu Sans"
        
    def fit_video_in_view(self):
        pass

class MockMainWindow:
    def __init__(self):
        self.selected_video_path = ""
        self.basic_tab = MockBasicTab()
        self.advance_tab = MockAdvanceTab()
        self.logs = []
        
    def log(self, msg):
        self.logs.append(msg)
        
    def reset_workspace(self):
        reset_workspace(self)

def test_reset_workspace():
    """
    Test reset_workspace restores default state values for MainWindow UI components.
    """
    mw = MockMainWindow()
    
    # Set non-default states
    mw.selected_video_path = "some_video.mp4"
    mw.basic_tab.selected_video_path = "some_video.mp4"
    mw.basic_tab.segments = [{"start": 10.0, "end": 20.0}]
    mw.advance_tab.selected_video_path = "some_video.mp4"
    mw.advance_tab.video_w = 1920
    mw.advance_tab.video_h = 1080
    
    reset_workspace(mw)
    
    assert mw.selected_video_path == ""
    assert mw.basic_tab.selected_video_path == ""
    assert mw.basic_tab.segments == []
    assert mw.advance_tab.selected_video_path == ""
    assert mw.advance_tab.video_w == 1280
    assert mw.advance_tab.video_h == 720
    
    mw.basic_tab.player.setSource.assert_called_once()
    mw.basic_tab.lbl_video_path.setText.assert_called_with("No video selected. Click 'Open Video' to select one.")
    mw.basic_tab.slider_timeline.setRange.assert_called_with(0, 0)
    mw.basic_tab.slider_timeline.setValue.assert_called_with(0)
    mw.basic_tab.lbl_time.setText.assert_called_with("00:00:00.000 / 00:00:00.000")
    mw.basic_tab.btn_play_pause.setText.assert_called_with("Play")
    
    mw.advance_tab.player.setSource.assert_called_once()
    mw.advance_tab.scene.clear.assert_called_once()
    mw.advance_tab.list_overlays.clear.assert_called_once()

def test_save_load_project_state(tmp_path):
    """
    Test save_project_state and load_project_state using tmp_path directory.
    """
    mw = MockMainWindow()
    
    # Path inside pytest tmp_path
    video_file = tmp_path / "test_video.mp4"
    video_file.touch() # Create dummy file
    video_path = str(video_file)
    
    mw.selected_video_path = video_path
    mw.advance_tab.chk_cuda.isChecked.return_value = True
    mw.advance_tab.chk_face_blur.isChecked.return_value = False
    mw.advance_tab.chk_bg_blur.isChecked.return_value = True
    mw.advance_tab.spin_bg_strength.value.return_value = 85
    
    # Text Overlays
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
    assert data["watermarks"]["advance_overlays"][0]["font_size"] == 24
    assert data["watermarks"]["advance_overlays"][0]["pos_x"] == 100.0
    assert data["watermarks"]["advance_overlays"][0]["pos_y"] == 150.0
    assert data["watermarks"]["advance_overlays"][0]["angle"] == 45.0
    assert data["watermarks"]["advance_overlays"][0]["opacity"] == 0.8
    
    # Let's test load_project_state
    # Clear settings on mw to see if loading works
    mw.advance_tab.chk_cuda.setChecked.reset_mock()
    mw.advance_tab.chk_bg_blur.setChecked.reset_mock()
    mw.advance_tab.spin_bg_strength.setValue.reset_mock()
    
    # Mocking QListWidgetItem creation and DraggableTextItem creation inside load_project_state
    with pytest.MonkeyPatch.context() as mp:
        mock_draggable_item_cls = MagicMock()
        mp.setattr("app.core.config_manager.DraggableTextItem", mock_draggable_item_cls)
        mock_list_item_cls = MagicMock()
        mp.setattr("app.core.config_manager.QListWidgetItem", mock_list_item_cls)
        
        load_project_state(mw, video_path)
        
        mw.advance_tab.chk_cuda.setChecked.assert_called_with(True)
        mw.advance_tab.chk_bg_blur.setChecked.assert_called_with(True)
        mw.advance_tab.spin_bg_strength.setValue.assert_called_with(85)
        
        # Verify DraggableTextItem was instantiated with proper attributes
        mock_draggable_item_cls.assert_called_once_with(
            text="Logo Text",
            font_size=24,
            angle=45.0,
            opacity=0.8,
            font_family="DejaVu Sans"
        )
