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

def get_ffmpeg_exact_cut_cmd(input_path: str, output_path: str, start_time: str, end_time: str) -> list[str]:
    """Build command for a precise, re-encoded cut."""
    return [
        "ffmpeg",
        "-i", input_path,
        "-ss", start_time,
        "-to", end_time,
        "-c:v", FFMPEG_CONFIGS["CPU_CODEC"], # Re-encode for accuracy
        "-preset", FFMPEG_CONFIGS["CPU_PRESET"],
        "-crf", FFMPEG_CONFIGS["CPU_CRF"],
        "-c:a", "aac", # Re-encode audio
        "-b:a", "192k",
        "-y",
        output_path
    ]

def get_ffmpeg_snapshot_cmd(input_path: str, output_path: str, time: str, quality: int, format: str) -> list[str]:
    """Build command to take a single snapshot."""
    cmd = [
        "ffmpeg",
        "-ss", time,
        "-i", input_path,
        "-frames:v", "1",
    ]
    if format.lower() == 'jpg':
        cmd.extend(["-q:v", str(quality)]) # Quality for JPG (1-31, lower is better)
    cmd.append(output_path)
    return cmd

def get_ffmpeg_export_cmd(input_path: str, output_path: str, options: dict) -> list[str]:
    """Build command for exporting with various options (FPS, tracks, metadata)."""
    cmd = ["ffmpeg", "-i", input_path]

    # Video and Audio filters
    video_filters = []
    if options.get("fps"):
        video_filters.append(f"fps={options['fps']}")

    if video_filters:
        cmd.extend(["-filter:v", ",".join(video_filters)])

    # Track handling
    if options.get('remove_audio'):
        cmd.append("-an")
    elif options.get('keep_audio', True):
        cmd.extend(["-map", "0:a?"])

    if options.get('remove_video'):
        cmd.append("-vn")
    elif options.get('keep_video', True):
        cmd.extend(["-map", "0:v?"])

    # Codec selection
    if not video_filters and not options.get('remove_audio') and not options.get('remove_video'):
        cmd.extend(["-c", "copy"]) # Default to stream copy if no filters/track removal
    else:
        cmd.extend(["-c:v", FFMPEG_CONFIGS["CPU_CODEC"], "-preset", FFMPEG_CONFIGS["CPU_PRESET"], "-crf", FFMPEG_CONFIGS["CPU_CRF"]])
        if not options.get('remove_audio'):
            cmd.extend(["-c:a", "aac", "-b:a", "192k"]) # Re-encode audio if video is re-encoded

    # Metadata
    if options.get('metadata'):
        cmd.extend(["-map_metadata", "-1"]) # Clear existing metadata
        for meta in options['metadata'].split('\n'):
            if '=' in meta:
                key, value = meta.split('=', 1)
                cmd.extend(["-metadata", f"{key.strip()}={value.strip()}"])
    else:
        cmd.extend(["-map_metadata", "0"]) # Keep original metadata

    cmd.extend(["-y", output_path])
    return cmd

