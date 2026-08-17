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
