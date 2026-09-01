import subprocess
import json
from app.core.constants import FFMPEG_COMMANDS, FFMPEG_FLAGS, VIDEO_CODECS
from app.core.ffmpeg_config import FFMPEG_CONFIGS, FFMPEG_PATH, FFPROBE_PATH
from app.core.ffmpeg_resolver import get_ffprobe_path, get_ffmpeg_path
from app.core.helpers import check_cuda_support, get_origin_bitrate, get_origin_tbn_fps
from app.services import ffmpeg_service

def get_video_keyframes(input_path: str) -> list[float]:
    """
    Sử dụng ffprobe để lấy toàn bộ timestamps (tính bằng giây) của các Keyframe (I-frames).
    """
    ffprobe_path = get_ffprobe_path()
    if not ffprobe_path:
        raise FileNotFoundError("ffprobe executable not found.")

    cmd = [
        FFPROBE_PATH,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_packets",
        "-show_entries", "packet=pts_time,flags",
        "-of", "json",
        input_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        keyframes = []
        for pkt in data.get("packets", []):
            flags = pkt.get("flags", "")
            # Trong ffprobe, cờ chứa 'K' (hoặc 'K_') biểu thị Keyframe
            if "K" in flags and "pts_time" in pkt:
                try:
                    keyframes.append(float(pkt["pts_time"]))
                except ValueError:
                    continue
        keyframes.sort()
        return keyframes
    except Exception as e:
        print(f"Error fetching keyframes: {e}")
        return []

def encode_subpart(input_path: str, start_sec: float, duration_sec: float, output_path: str):
    """Hàm mã hóa chính xác một đoạn cực ngắn với bitrate tương đương file gốc."""
    raw_bitrate = get_origin_bitrate(input_path)
    bitrate_str = raw_bitrate if raw_bitrate else FFMPEG_CONFIGS["VIDEO_BITRATE_DEFAULT"]
    start_str = ffmpeg_service.format_seconds_to_time(start_sec)
    use_gpu = check_cuda_support()
    fps_tbn = get_origin_tbn_fps(input_path)
    # print(f"Encoding subpart info - fps_tbn={fps_tbn[0]} {fps_tbn[1]}")
    
    cmd = [
        FFMPEG_PATH, FFMPEG_COMMANDS.OVERWRITE_OUTPUT,
        FFMPEG_COMMANDS.SEEK, start_str,
        FFMPEG_COMMANDS.INPUT, input_path,
        FFMPEG_COMMANDS.TT, f"{duration_sec:.6f}",
        FFMPEG_COMMANDS.MAP, "0:v:0",
        FFMPEG_COMMANDS.MAP, "0:a:0?",
        FFMPEG_COMMANDS.VIDEO_CODEC, VIDEO_CODECS.CPU_H264,
        FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["CPU_PRESET"],
        FFMPEG_COMMANDS.FRAME_RATE, fps_tbn[0],
        FFMPEG_COMMANDS.PIXEL_FORMAT, "yuv420p",
        # FFMPEG_COMMANDS.VIDEO_TRACK_TIMESCALE, fps_tbn[1],
        FFMPEG_COMMANDS.AUDIO_CODEC, "copy",
        FFMPEG_COMMANDS.VIDEO_BITRATE, bitrate_str,
        FFMPEG_FLAGS.AVOID_NEGATIVE_TS, FFMPEG_FLAGS.MAKE_ZERO,
        output_path
    ]

    gpu_cmd = [
        FFMPEG_PATH, FFMPEG_COMMANDS.OVERWRITE_OUTPUT, FFMPEG_COMMANDS.HARDWARE_ACCE, FFMPEG_CONFIGS["HWACCEL_CUDA"],
        # FFMPEG_COMMANDS.HARDWARE_OUTPUT_ACCE, FFMPEG_CONFIGS["HWACCEL_CUDA"],
        FFMPEG_COMMANDS.SEEK, start_str,
        FFMPEG_COMMANDS.INPUT, input_path,
        FFMPEG_COMMANDS.TT, f"{duration_sec:.6f}",
        FFMPEG_COMMANDS.MAP, "0:v:0",
        FFMPEG_COMMANDS.MAP, "0:a:0?",
        FFMPEG_COMMANDS.VIDEO_CODEC, VIDEO_CODECS.NVENC_H264,
        FFMPEG_COMMANDS.RC_OPTION, FFMPEG_CONFIGS["RC_VALUE"],
        FFMPEG_COMMANDS.MULTIPASS_OPTION , FFMPEG_CONFIGS["MULTIPASS_VAL"],
        FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["NVENC_PRESET"],
        FFMPEG_COMMANDS.FRAME_RATE, fps_tbn[0],
        FFMPEG_COMMANDS.PIXEL_FORMAT, "yuv420p",
        # FFMPEG_COMMANDS.VIDEO_TRACK_TIMESCALE, fps_tbn[1],
        FFMPEG_COMMANDS.AUDIO_CODEC, "copy",
        FFMPEG_COMMANDS.VIDEO_BITRATE, bitrate_str,
        FFMPEG_FLAGS.AVOID_NEGATIVE_TS, FFMPEG_FLAGS.MAKE_ZERO,
        output_path
    ]

    final_cmd = gpu_cmd if use_gpu else cmd
    subprocess.run(final_cmd, capture_output=True, text=True, check=True)

def plan_smart_cut_segment(start: float, end: float, keyframes: list[float]) -> list[dict]:
    """
    Phân tích một segment (start -> end) dựa trên danh sách Keyframes.
    Trả về danh sách các sub-parts gồm:
    - 'encode': Re-encode từ mốc start tới Keyframe
    - 'copy': Copy lossless từ Keyframe tới Keyframe
    """
    if start >= end:
        return []

    if not keyframes:
        # Nếu không lấy được Keyframe, fallback về re-encode toàn bộ segment
        return [{"type": "encode", "start": start, "end": end}]

    # Tìm Keyframe đầu tiên >= start
    first_kf_after_start = next((k for k in keyframes if k >= start), None)
    
    # Tìm Keyframe cuối cùng <= end
    last_kf_before_end = next((k for k in reversed(keyframes) if k <= end), None)

    # Trường hợp 1: Cả segment nằm trọn trong khoảng giữa 2 Keyframe (không chứa Keyframe nào)
    if first_kf_after_start is None or first_kf_after_start > end or last_kf_before_end < start:
        return [{"type": "encode", "start": start, "end": end}]

    # Trường hợp 2: Khớp hoàn toàn vào điểm Keyframe (không cần encode)
    parts = []
    
    # 1. Đoạn Head (Re-encode phần đầu nếu start không trùng Keyframe)
    if start < first_kf_after_start:
        if first_kf_after_start <= end:
            parts.append({"type": "encode", "start": start, "end": first_kf_after_start})
            current_pos = first_kf_after_start
        else:
            parts.append({"type": "encode", "start": start, "end": end})
            return parts
    else:
        current_pos = start

    # 2. Đoạn Body (Lossless copy phần giữa giữa các Keyframes)
    if last_kf_before_end > current_pos:
        parts.append({"type": "copy", "start": current_pos, "end": last_kf_before_end})
        current_pos = last_kf_before_end

    # 3. Đoạn Tail (Re-encode phần đuôi nếu end không trùng Keyframe)
    if current_pos < end:
        parts.append({"type": "encode", "start": current_pos, "end": end})

    return parts