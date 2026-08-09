import os
import json
from PyQt6.QtCore import QUrl, QSizeF, Qt
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtWidgets import QLineEdit

def reset_workspace(main_window):
    """
    Reset all workspaces (Basic and Advanced tabs) to default empty states.
    """
    main_window.selected_video_path = ""
    
    # 1. Reset BasicCutTab
    main_window.basic_tab.player.setSource(QUrl())
    main_window.basic_tab.selected_video_path = ""
    main_window.basic_tab.lbl_video_path.setText("No video selected. Click 'Open Video' to select one.")
    main_window.basic_tab.slider_timeline.setRange(0, 0)
    main_window.basic_tab.slider_timeline.setValue(0)
    main_window.basic_tab.lbl_time.setText("00:00:00.000 / 00:00:00.000")
    main_window.basic_tab.btn_play_pause.setText("Play")
    main_window.basic_tab.segments = []
    main_window.basic_tab.update_segments_table_without_save()
    main_window.basic_tab.txt_manual_start.setText("")
    main_window.basic_tab.txt_manual_end.setText("")
    main_window.basic_tab.txt_watermark.setText("")
    main_window.basic_tab.cb_position.setCurrentIndex(0)
    
    # 2. Reset AdvanceWatermarkTab
    main_window.advance_tab.player.setSource(QUrl())
    main_window.advance_tab.selected_video_path = ""
    main_window.advance_tab.slider_timeline.setRange(0, 0)
    main_window.advance_tab.slider_timeline.setValue(0)
    main_window.advance_tab.lbl_time.setText("00:00:00.000 / 00:00:00.000")
    main_window.advance_tab.btn_play_pause.setText("Play")
    
    # Recreate video item and clear scene
    main_window.advance_tab.scene.clear()
    main_window.advance_tab.video_item = QGraphicsVideoItem()
    main_window.advance_tab.scene.addItem(main_window.advance_tab.video_item)
    main_window.advance_tab.video_item.setZValue(0)
    main_window.advance_tab.player.setVideoOutput(main_window.advance_tab.video_item)
    
    # Reset scene rect
    main_window.advance_tab.video_w, main_window.advance_tab.video_h = 1280, 720
    main_window.advance_tab.scene.setSceneRect(0, 0, 1280, 720)
    main_window.advance_tab.video_item.setPos(0, 0)
    main_window.advance_tab.video_item.setSize(QSizeF(1280.0, 720.0))
    main_window.advance_tab.fit_video_in_view()
    
    main_window.advance_tab.text_items = []
    main_window.advance_tab.list_overlays.clear()
    main_window.advance_tab.selected_item = None
    
    # Reset all inputs
    main_window.advance_tab.txt_overlay_text.setText("")
    main_window.advance_tab.txt_face_image_path.setText("")
    main_window.advance_tab.chk_cuda.setChecked(False)
    main_window.advance_tab.chk_face_blur.setChecked(False)
    main_window.advance_tab.chk_bg_blur.setChecked(False)
    main_window.advance_tab.spin_font_size.setValue(32)
    main_window.advance_tab.slider_rotation.setValue(0)
    main_window.advance_tab.slider_opacity.setValue(100)
    main_window.advance_tab.spin_face_blur_pct.setValue(0)
    main_window.advance_tab.spin_face_blur_strength.setValue(15)
    main_window.advance_tab.spin_bg_strength.setValue(101)
    main_window.advance_tab.cb_face_blur_type.setCurrentIndex(0)
    main_window.advance_tab.cb_face_blur_style.setCurrentIndex(0)
    
    # Hide replacement image widget
    main_window.advance_tab.widget_face_image.setVisible(False)


def save_project_state(main_window):
    """
    Save the current project state of the MainWindow to a JSON file named `<video_name>.json`.
    """
    video_path = main_window.selected_video_path
    if not video_path:
        return
    
    json_path = os.path.splitext(video_path)[0] + ".json"
    
    # Need formatting function for saving
    from app.services.ffmpeg_service import format_seconds_to_time
    
    # 1. basic_cut
    cuts = []
    for seg in main_window.basic_tab.segments:
        start_str = format_seconds_to_time(seg["start"], include_ms=False)
        end_str = format_seconds_to_time(seg["end"], include_ms=False)
        cuts.append({"start": start_str, "end": end_str})
    
    basic_cut_data = {
        "enabled": len(cuts) > 0,
        "cuts": cuts
    }
    
    # 2. watermarks
    top_text = None
    mid_text = None
    bot_text = None
    
    advance_overlays = []
    for item in main_window.advance_tab.text_items:
        advance_overlays.append({
            "text": item.toPlainText(),
            "font_size": item.font_size,
            "pos_x": float(item.pos().x()),
            "pos_y": float(item.pos().y()),
            "angle": float(item.angle),
            "opacity": float(item.opacity_val)
        })
        
    watermarks_data = {
        "top_text": top_text,
        "mid_text": mid_text,
        "bot_text": bot_text,
        "advance_overlays": advance_overlays
    }
    
    # 3. face_blur
    face_blur_data = {
        "enabled": main_window.advance_tab.chk_face_blur.isChecked(),
        "shape": main_window.advance_tab.cb_face_blur_type.currentData() or "Square",
        "style": main_window.advance_tab.cb_face_blur_style.currentData() or "Gaussian",
        "strength": main_window.advance_tab.spin_face_blur_strength.value(),
        "pad_ratio": main_window.advance_tab.spin_face_blur_pct.value() / 100.0
    }
    
    # 4. bg_blur
    bg_blur_data = {
        "enabled": main_window.advance_tab.chk_bg_blur.isChecked(),
        "amount": main_window.advance_tab.spin_bg_strength.value() if main_window.advance_tab.chk_bg_blur.isChecked() else None
    }
    
    # Save complete JSON state
    data = {
        "video_path": video_path,
        "hardware_acceleration": main_window.advance_tab.chk_cuda.isChecked(),
        "basic_cut": basic_cut_data,
        "watermarks": watermarks_data,
        "face_blur": face_blur_data,
        "bg_blur": bg_blur_data
    }
    
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        main_window.log(f"Project state saved to {os.path.basename(json_path)}")
    except Exception as e:
        main_window.log(f"Failed to save project state: {str(e)}")


def load_project_state(main_window, video_path):
    """
    Load project state from a `<video_name>.json` file.
    """
    if not video_path:
        return
        
    json_path = os.path.splitext(video_path)[0] + ".json"
    
    if not os.path.exists(json_path):
        main_window.log(f"No JSON project file found at {json_path}. Resetting workspace.")
        main_window.reset_workspace()
        return
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        main_window.log(f"Failed to read project JSON: {str(e)}")
        main_window.reset_workspace()
        return
        
    from app.services.ffmpeg_service import parse_time_to_seconds
    from app.ui.advance_watermark_tab import DraggableTextItem
    from PyQt6.QtWidgets import QListWidgetItem
    
    # Safe loading with .get(key, default) as instructed
    main_window.log(f"Loading project state from {os.path.basename(json_path)}")
    
    # 1. Hardware acceleration
    hw_accel = data.get("hardware_acceleration", False)
    main_window.advance_tab.chk_cuda.setChecked(bool(hw_accel))
    
    # 2. basic_cut
    basic_cut = data.get("basic_cut")
    if isinstance(basic_cut, dict):
        cuts = basic_cut.get("cuts", [])
        main_window.basic_tab.segments = []
        for cut in cuts:
            if isinstance(cut, dict):
                start_str = cut.get("start", "00:00:00")
                end_str = cut.get("end", "00:00:00")
                start_sec = parse_time_to_seconds(start_str)
                end_sec = parse_time_to_seconds(end_str)
                main_window.basic_tab.segments.append({"start": start_sec, "end": end_sec})
        main_window.basic_tab.update_segments_table_without_save()
        
    # 3. watermarks & advance_overlays
    # Let's clear previous text items first
    for item in main_window.advance_tab.text_items:
        try:
            main_window.advance_tab.scene.removeItem(item)
        except Exception:
            pass
    main_window.advance_tab.text_items.clear()
    main_window.advance_tab.list_overlays.clear()
    main_window.advance_tab.selected_item = None
    
    watermarks = data.get("watermarks")
    if isinstance(watermarks, dict):
        advance_overlays = watermarks.get("advance_overlays", [])
        for ov in advance_overlays:
            if isinstance(ov, dict):
                text_str = ov.get("text", "Text")
                font_size = ov.get("font_size", 32)
                pos_x = ov.get("pos_x", 50.0)
                pos_y = ov.get("pos_y", 50.0)
                angle = ov.get("angle", 0.0)
                opacity = ov.get("opacity", 1.0)
                
                # Create the DraggableTextItem
                item = DraggableTextItem(
                    text=text_str, 
                    font_size=font_size, 
                    angle=angle, 
                    opacity=opacity, 
                    font_family=main_window.advance_tab.app_font_family
                )
                item.setZValue(100 + len(main_window.advance_tab.text_items))
                item.setPos(pos_x, pos_y)
                
                main_window.advance_tab.scene.addItem(item)
                main_window.advance_tab.text_items.append(item)
                
                list_item = QListWidgetItem(text_str)
                main_window.advance_tab.list_overlays.addItem(list_item)
                
    # 4. face_blur
    face_blur = data.get("face_blur")
    if isinstance(face_blur, dict):
        enabled = face_blur.get("enabled", False)
        shape = face_blur.get("shape", "Square")
        style = face_blur.get("style", "Gaussian")
        strength = face_blur.get("strength", 15)
        pad_ratio = face_blur.get("pad_ratio", 0.0)
        
        main_window.advance_tab.chk_face_blur.setChecked(bool(enabled))
        
        # Find shape index in cb_face_blur_type
        idx = main_window.advance_tab.cb_face_blur_type.findData(shape)
        if idx >= 0:
            main_window.advance_tab.cb_face_blur_type.setCurrentIndex(idx)
            
        # Find style index in cb_face_blur_style
        idx = main_window.advance_tab.cb_face_blur_style.findData(style)
        if idx >= 0:
            main_window.advance_tab.cb_face_blur_style.setCurrentIndex(idx)
            
        main_window.advance_tab.spin_face_blur_strength.setValue(int(strength))
        main_window.advance_tab.spin_face_blur_pct.setValue(int(pad_ratio * 100.0))
        
    # 5. bg_blur
    bg_blur = data.get("bg_blur")
    if isinstance(bg_blur, dict):
        enabled = bg_blur.get("enabled", False)
        amount = bg_blur.get("amount")
        
        main_window.advance_tab.chk_bg_blur.setChecked(bool(enabled))
        if amount is not None:
            main_window.advance_tab.spin_bg_strength.setValue(int(amount))
