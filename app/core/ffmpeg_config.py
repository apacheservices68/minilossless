# FFmpeg Configuration and command builder helper functions

# Dictionary to store all configuration options
FFMPEG_CONFIGS = {
    "CPU_CODEC": "libx264",
    "CPU_PRESET": "fast",
    "CPU_CRF": "22",
    "NVENC_CODEC": "h264_nvenc",
    "NVENC_PRESET": "p4",
    "PIX_FMT": "yuv420p",
    "RAW_PIX_FMT": "bgr24",
    "BITRATE": None,
    "QP": None,
    "GOP_SIZE": None,
}

def get_ffmpeg_cut_cmd(input_path: str, output_path: str, start_time: str, end_time: str) -> list[str]:
    """
    Build command list to cut video.
    """
    return [
        "ffmpeg",
        "-ss", start_time,
        "-to", end_time,
        "-i", input_path,
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        "-y",
        output_path
    ]

def get_ffmpeg_merge_cmd(temp_list: str, output_path: str) -> list[str]:
    """
    Build command list to merge multiple videos using concat demuxer.
    """
    return [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", temp_list,
        "-c", "copy",
        "-y",
        output_path
    ]

def get_ffmpeg_watermark_cmd(input_path: str, output_path: str, temp_watermark: str, coords: str) -> list[str]:
    """
    Build command list to add a basic text watermark overlay.
    """
    return [
        "ffmpeg",
        "-i", input_path,
        "-i", temp_watermark,
        "-filter_complex", f"[0:v][1:v]overlay={coords}[outv]",
        "-map", "[outv]",
        "-map", "0:a?",
        "-c:v", FFMPEG_CONFIGS["CPU_CODEC"],
        "-preset", FFMPEG_CONFIGS["CPU_PRESET"],
        "-crf", FFMPEG_CONFIGS["CPU_CRF"],
        "-y",
        output_path
    ]

def get_ffmpeg_pipe_cmd(
    width: int,
    height: int,
    fps: float,
    temp_watermark_path: str,
    input_video_path: str,
    use_cuda: bool,
    output_video_path: str
) -> list[str]:
    """
    Build command list to push raw video frames to FFmpeg pipe.
    """
    # Base command
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", FFMPEG_CONFIGS["RAW_PIX_FMT"],
        "-s", f"{width}x{height}",
        "-r", f"{fps}",
        "-i", "-", 
        "-i", temp_watermark_path,
        "-i", input_video_path,
        "-filter_complex", "[0:v][1:v]overlay=0:0[outv]",
        "-map", "[outv]",
        "-map", "2:a?",
    ]
    
    # Optional parameters can be added to the dictionary to support bitrate, QP, gop size
    # E.g., if FFMPEG_CONFIGS["GOP_SIZE"] is not None:
    #       cmd.extend(["-g", str(FFMPEG_CONFIGS["GOP_SIZE"])])
    
    if use_cuda:
        cmd.extend([
            "-c:v", FFMPEG_CONFIGS["NVENC_CODEC"],
            "-preset", FFMPEG_CONFIGS["NVENC_PRESET"],
            "-pix_fmt", FFMPEG_CONFIGS["PIX_FMT"]
        ])
    else:
        cmd.extend([
            "-c:v", FFMPEG_CONFIGS["CPU_CODEC"],
            "-preset", FFMPEG_CONFIGS["CPU_PRESET"],
            "-crf", FFMPEG_CONFIGS["CPU_CRF"],
            "-pix_fmt", FFMPEG_CONFIGS["PIX_FMT"]
        ])
        
    if FFMPEG_CONFIGS["BITRATE"] is not None:
        cmd.extend(["-b:v", FFMPEG_CONFIGS["BITRATE"]])
    if FFMPEG_CONFIGS["QP"] is not None:
        cmd.extend(["-qp", str(FFMPEG_CONFIGS["QP"])])
    if FFMPEG_CONFIGS["GOP_SIZE"] is not None:
        cmd.extend(["-g", str(FFMPEG_CONFIGS["GOP_SIZE"])])
        
    cmd.append(output_video_path)
    return cmd
