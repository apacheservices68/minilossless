import json
import os
import cv2
import math
import subprocess

def check_cuda_support():
    try:
        if hasattr(cv2, 'cuda') and cv2.cuda.getCudaEnabledDeviceCount() > 0:
            return True
    except Exception:
        pass

    try:
        cmd = "nvidia-smi.exe" if os.name == "nt" else "nvidia-smi"
        res = subprocess.run([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        if res.returncode == 0:
            return True
    except Exception:
        pass
        
    return False

def get_media_info(file_path):
    """Lấy thông tin video resolution dùng ffprobe trực tiếp"""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error running ffprobe: {e}")
        return {"streams": []}

def format_ms_to_timecode(ms: int) -> str:
    if ms is None or ms < 0:
        return "00:00:00.000"
    seconds = ms / 1000.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(ms % 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"

def timecode_to_ms(timecode_str: str) -> int:
    if not timecode_str or timecode_str == "00:00:00.000":
        return 0
    try:
        # Tách phần giờ:phút:giây và miligiây
        parts = timecode_str.strip().split(":")
        if len(parts) == 3:
            hrs = int(parts[0])
            mins = int(parts[1])
            secs_parts = parts[2].split(".")
            secs = int(secs_parts[0])
            millis = int(secs_parts[1]) if len(secs_parts) > 1 else 0
            
            total_ms = (hrs * 3600 + mins * 60 + secs) * 1000 + millis
            return total_ms
    except Exception:
        pass
    return 0

def calculate_relative_text_overlays(text_items, video_item):
    if not video_item:
        return []
        
    item_rect = video_item.boundingRect()
    v_w = max(1.0, item_rect.width())
    v_h = max(1.0, item_rect.height())
    v_diag = math.hypot(v_w, v_h)

    texts_to_backend = []
    for item in text_items:
        scene_center = item.mapToItem(video_item, item.boundingRect().center())
        rel_center_x = scene_center.x() / v_w
        rel_center_y = scene_center.y() / v_h
        
        rel_font_size = item.font_size / v_diag

        texts_to_backend.append({
            "text": item.toPlainText(),
            "rel_center_x": rel_center_x,
            "rel_center_y": rel_center_y,
            "rel_font_size": rel_font_size,
            "rotation_angle": item.angle,
            "opacity": item.opacity_val
        })
    return texts_to_backend
