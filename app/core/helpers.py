import json
import os
import re
import cv2
import math
import subprocess

def parse_ffmpeg_progress(line: str, duration_sec: float) -> int | None:
    """
    Parse log FFmpeg và trả về % tiến độ (0 - 100).
    """
    if duration_sec <= 0:
        return None

    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
    match = time_pattern.search(line)
    if match:
        hours, minutes, seconds = map(float, match.groups())
        elapsed = hours * 3600 + minutes * 60 + seconds
        pct = int((elapsed / duration_sec) * 100)
        return min(100, max(0, pct))

    return None

def export_video_with_progress(cmd, duration_sec, progress_callback=None):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        universal_newlines=True
    )

    for line in process.stdout:
        if progress_callback:
            pct = parse_ffmpeg_progress(line, duration_sec)
            if pct is not None:
                progress_callback(pct, f"Exporting: {pct}%")

    process.wait()
    return process.returncode == 0

def check_cuda_support():
    try:
        if hasattr(cv2, 'cuda') and cv2.cuda.getCudaEnabledDeviceCount() > 0:
            return True
    except Exception:
        pass

    try:

        # Kiểm tra xem ffmpeg có hỗ trợ h264_nvenc encoder không
        result = subprocess.run(
            ["ffmpeg", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        if "h264_nvenc" in result.stdout:
            return True
        
        cmd = "nvidia-smi.exe" if os.name == "nt" else "nvidia-smi"
        res = subprocess.run([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        if res.returncode == 0:
            return True
    except Exception:
        pass
        
    return False

def calculate_cropped_bitrate(orig_w: int, orig_h: int, crop_w: int, crop_h: int, orig_bitrate_bps: int) -> str:
    """
    Tính bitrate mới dựa trên tỉ lệ diện tích crop.
    Trả về chuỗi dạng "4166k" dùng cho cờ -b:v của FFmpeg.
    """
    if orig_w <= 0 or orig_h <= 0 or orig_bitrate_bps <= 0:
        return None

    orig_area = orig_w * orig_h
    crop_area = crop_w * crop_h

    # Tỉ lệ diện tích giữ lại
    ratio = crop_area / float(orig_area)
    
    # Tính bitrate mới (bps -> kbps)
    new_bitrate_kbps = int((orig_bitrate_bps * ratio) / 1000)
    
    # Đảm bảo bitrate không bị tụt quá thấp gây mờ hình (tối thiểu 800k)
    new_bitrate_kbps = max(new_bitrate_kbps, 800)

    return f"{new_bitrate_kbps}k"

def get_origin_bitrate(input_path):
    info = get_media_info(input_path)
    video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    orig_bitrate = None
    if "bit_rate" in info.get("format", {}):
        orig_bitrate = int(info["format"]["bit_rate"])
    elif "bit_rate" in video_stream:
        orig_bitrate = int(video_stream["bit_rate"])

    return f"{int(orig_bitrate / 1000)}k" if orig_bitrate is not None else None

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
