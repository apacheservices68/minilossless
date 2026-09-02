import subprocess
import json
import os
from app.core.constants import FFMPEG_COMMANDS, FFMPEG_FLAGS, FFPROBE_FLAGS, VIDEO_CODECS
from app.core.ffmpeg_config import FFMPEG_CONFIGS
from app.core.ffmpeg_resolver import get_ffprobe_path, get_ffmpeg_path
from app.core.helpers import get_origin_bitrate, get_origin_tbn_fps

def is_iphone_or_hevc(input_path: str) -> bool:
    """Check xem file có phải .mov hoặc codec video là HEVC/H.265 hay không."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".mov":
        return True

    ffprobe_path = get_ffprobe_path() or "ffprobe"
    cmd = [
        ffprobe_path,
        "-v", "error",
        FFPROBE_FLAGS.SELECT_STREAMS_VIDEO, "v:0",
        FFPROBE_FLAGS.SHOW_ENTRIES, "stream=codec_name",
        FFPROBE_FLAGS.OF_JSON, "json",
        input_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        if streams:
            codec_name = streams[0].get("codec_name", "").lower()
            if codec_name in ["hevc", "h265"]:
                return True
    except Exception as e:
        print(f"[Probe Check Warning] Couldn't detect codec: {e}")

    return False

def get_video_keyframes(input_path: str) -> list[float]:
    """Lấy danh sách PTS Timestamp của các Keyframe bằng ffprobe."""
    ffprobe_path = get_ffprobe_path() or "ffprobe"

    cmd = [
        ffprobe_path,
        "-v", "error",
        FFPROBE_FLAGS.SELECT_STREAMS_VIDEO, "v:0",
        FFPROBE_FLAGS.SHOW_PACKETS,
        FFPROBE_FLAGS.SHOW_ENTRIES, "packet=pts_time,flags",
        FFPROBE_FLAGS.OF_JSON, "json",
        input_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        keyframes = []
        for pkt in data.get("packets", []):
            flags = pkt.get("flags", "")
            if "K" in flags and "pts_time" in pkt and pkt["pts_time"] is not None:
                try:
                    keyframes.append(float(pkt["pts_time"]))
                except ValueError:
                    continue
        keyframes.sort()
        return keyframes
    except Exception as e:
        print(f"[Keyframe Error] Failed to read keyframes: {e}")
        return []

def plan_smart_cut_segment(start: float, end: float, keyframes: list[float], input_path: str = None) -> list[dict]:
    """
    Phân hoạch segment: 
    Nếu là iPhone/MOV/HEVC -> Ép Encode toàn bộ đoạn để tránh lỗi xanh màn/mất tiếng.
    """
    if start >= end:
        return []

    # Check điều kiện đặc biệt cho file MOV / HEVC
    if input_path and is_iphone_or_hevc(input_path):
        return [{"type": "encode", "start": start, "end": end}]

    if not keyframes:
        return [{"type": "encode", "start": start, "end": end}]

    first_kf_after_start = next((k for k in keyframes if k >= start), None)

    if first_kf_after_start is None or first_kf_after_start >= end:
        return [{"type": "encode", "start": start, "end": end}]

    last_kf_before_end = next((k for k in reversed(keyframes) if k <= end), None)

    parts = []
    current_pos = start

    # Head Re-encode
    if abs(start - first_kf_after_start) > 0.001:
        parts.append({"type": "encode", "start": start, "end": first_kf_after_start})
        current_pos = first_kf_after_start

    # Body Lossless Copy
    if last_kf_before_end is not None and last_kf_before_end > current_pos:
        parts.append({"type": "copy", "start": current_pos, "end": last_kf_before_end})
        current_pos = last_kf_before_end

    # Tail Re-encode
    if abs(end - current_pos) > 0.001:
        parts.append({"type": "encode", "start": current_pos, "end": end})

    return parts

def cut_copy_subpart(input_path: str, start_sec: float, duration_sec: float, output_path: str, timescale: str = None):
    """Cắt đoạn video lossless copy chính xác chuẩn LosslessCut."""
    ffmpeg_bin = get_ffmpeg_path() or "ffmpeg"
    
    cmd = [
        ffmpeg_bin,
        FFMPEG_FLAGS.HIDE_BANNER,
        FFMPEG_FLAGS.YES,
        FFMPEG_FLAGS.START_TIME, f"{start_sec:.5f}",
        "-i", input_path,
        FFMPEG_FLAGS.DURATION, f"{duration_sec:.5f}",
        FFMPEG_FLAGS.MAP, "0:v:0",
        "-c:v", VIDEO_CODECS.COPY,
        FFMPEG_FLAGS.MAP, "0:a:0?",
        "-c:a", VIDEO_CODECS.COPY,
        FFMPEG_FLAGS.MAP_METADATA, "0",
        FFMPEG_FLAGS.MOVFLAGS, FFMPEG_FLAGS.FASTSTART,
        FFMPEG_FLAGS.DEFAULT_MODE, FFMPEG_FLAGS.INFER_NO_SUBS,
        FFMPEG_FLAGS.IGNORE_UNKNOWN
    ]
    
    if timescale and timescale != "0":
        cmd.extend([FFMPEG_FLAGS.VIDEO_TIMESCALE, timescale])

    cmd.append(output_path)
    subprocess.run(cmd, capture_output=True, text=True, check=True)

def encode_subpart(input_path: str, start_sec: float, duration_sec: float, output_path: str):
    """Re-encode đoạn ngắn sát keyframe, dùng hằng số chuẩn."""
    ffmpeg_bin = get_ffmpeg_path() or "ffmpeg"
    raw_bitrate = get_origin_bitrate(input_path)
    bitrate_str = raw_bitrate if raw_bitrate else FFMPEG_CONFIGS["VIDEO_BITRATE_DEFAULT"]
    fps_tbn = get_origin_tbn_fps(input_path)

    cmd = [
        ffmpeg_bin,
        FFMPEG_FLAGS.HIDE_BANNER,
        FFMPEG_FLAGS.YES,
        FFMPEG_FLAGS.START_TIME, f"{start_sec:.5f}",
        "-i", input_path,
        FFMPEG_FLAGS.START_TIME, "0",
        FFMPEG_FLAGS.DURATION, f"{duration_sec:.5f}",
        FFMPEG_FLAGS.MAP, "0:v:0",
        FFMPEG_FLAGS.MAP, "0:a:0?",
        "-c:v", VIDEO_CODECS.CPU_H264,
        "-b:v", bitrate_str,
        "-c:a", VIDEO_CODECS.COPY,
        FFMPEG_FLAGS.IGNORE_UNKNOWN
    ]

    if len(fps_tbn) > 1 and fps_tbn[1] != "0":
        cmd.extend([FFMPEG_FLAGS.VIDEO_TIMESCALE, fps_tbn[1]])
        cmd.extend([FFMPEG_COMMANDS.FRAME_RATE, fps_tbn[0]])

    cmd.append(output_path)
    subprocess.run(cmd, capture_output=True, text=True, check=True)