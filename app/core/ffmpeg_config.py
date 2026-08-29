from app.core.ffmpeg_resolver import get_ffmpeg_path
from app.core.constants import VIDEO_CODECS, HW_ACCELS, FFMPEG_COMMANDS, FFMPEG_FLAGS, PIXEL_FORMATS

# FFmpeg Configuration and command builder helper functions

FFMPEG_PATH = get_ffmpeg_path()

# Dictionary to store all configuration options
FFMPEG_CONFIGS = {
    # CPU Encoding
    "CPU_CODEC": VIDEO_CODECS.CPU_H264,
    "CPU_PRESET": "fast",
    "CPU_CRF": "22",

    # NVIDIA NVENC
    "NVENC_H264_CODEC": VIDEO_CODECS.NVENC_H264,
    "NVENC_HEVC_CODEC": VIDEO_CODECS.NVENC_HEVC,
    "NVENC_PRESET": "p4",

    # Intel QSV
    "QSV_H264_CODEC": VIDEO_CODECS.QSV_H264,

    # AMD AMF
    "AMF_H264_CODEC": VIDEO_CODECS.AMF_H264,

    # VAAPI (Linux)
    "VAAPI_H264_CODEC": VIDEO_CODECS.VAAPI_H264,
    
    # Hardware Acceleration Flags
    "HWACCEL_CUDA": HW_ACCELS.CUDA,
    "HWACCEL_AUTO": HW_ACCELS.AUTO,

    # Pixel Formats
    "PIX_FMT": PIXEL_FORMATS.YUV420P,
    "RAW_PIX_FMT": PIXEL_FORMATS.BGR24,

    # Audio
    "AUDIO_CODEC_AAC": VIDEO_CODECS.AAC,
    "AUDIO_BITRATE_192K": "192k",

    # CUDA Optional Parameters for bitrate, QP, and gop size 
    "BITRATE": None,
    "QP": "26",
    "GOP_SIZE": "60",
    ## Add on 08232026 
    "RC_VALUE": "vbr",
    "SCENECUT" : None,
    "MAX_MUTE_QUEUE_VAL" : "9999",
    "TUNE_VAL" : "6",
    "SPATIAL_VAL": "1",
    "TEMPORAL_VAL": "1",
    "LOOKAHEAD_VAL" : "32",
    "A_MUTE" : "-an",
    "MULTIPASS_VAL" : "qres",
    "CQ": "28",
    "MAXRATE_VAL" : "12M",
    "BUFFSIZE_VAL" : "12M"
}

def get_ffmpeg_cut_cmd(input_path: str, output_path: str, start_time: str, end_time: str, tracks: list = None, audio_codec: str = "copy") -> list[str]:
    """
    Build command list for lossless video cutting.
    """
    if not FFMPEG_PATH:
        raise FileNotFoundError("FFmpeg executable not found. Please install it and add to your PATH.")

    cmd = [FFMPEG_PATH, FFMPEG_COMMANDS.OVERWRITE_OUTPUT, FFMPEG_COMMANDS.SEEK, start_time, FFMPEG_COMMANDS.INPUT, input_path, FFMPEG_COMMANDS.TO, end_time]

    if tracks:
        map_flags = []
        metadata_flags = []
        output_stream_index = 0
        for track in tracks:
            if track.get("enabled", True):
                stream_index = track["index"]
                map_flags.extend([FFMPEG_COMMANDS.MAP, f"0:{stream_index}"])

                if "tags" in track:
                    for key, value in track["tags"].items():
                        metadata_flags.extend([f"{FFMPEG_COMMANDS.METADATA}:s:{output_stream_index}", f"{key}={value}"])
                output_stream_index += 1
        cmd.extend(map_flags)
        cmd.extend(metadata_flags)

    if audio_codec:
        cmd.extend([FFMPEG_COMMANDS.COPY_CODEC, audio_codec])
    else:
        cmd.extend(["-vn"]) # No audio

    cmd.extend([FFMPEG_FLAGS.AVOID_NEGATIVE_TS, FFMPEG_FLAGS.MAKE_ZERO, "-movflags", FFMPEG_FLAGS.FASTSTART])
    cmd.append(output_path)
    return cmd

def get_ffmpeg_merge_cmd(temp_list: str, output_path: str) -> list[str]:
    """
    Build command list for merging videos from a text file.
    """
    if not FFMPEG_PATH:
        raise FileNotFoundError("FFmpeg executable not found. Please install it and add to your PATH.")
    return [
        FFMPEG_PATH,
        "-f", FFMPEG_FLAGS.CONCAT,
        FFMPEG_FLAGS.SAFE, "0",
        FFMPEG_COMMANDS.INPUT, temp_list,
        FFMPEG_COMMANDS.COPY_CODEC, "copy",
        FFMPEG_COMMANDS.OVERWRITE_OUTPUT,
        output_path
    ]

def get_ffmpeg_watermark_cmd(input_path: str, output_path: str, temp_watermark: str, coords: str) -> list[str]:
    """
    Build command list to add a basic text watermark overlay.
    """
    if not FFMPEG_PATH:
        raise FileNotFoundError("FFmpeg executable not found. Please install it and add to your PATH.")
    return [
        FFMPEG_PATH,
        FFMPEG_COMMANDS.INPUT, input_path,
        FFMPEG_COMMANDS.INPUT, temp_watermark,
        "-filter_complex", f"[0:v][1:v]overlay={coords}[outv]",
        FFMPEG_COMMANDS.MAP, "[outv]",
        FFMPEG_COMMANDS.MAP, "0:a?",
        FFMPEG_COMMANDS.VIDEO_CODEC, FFMPEG_CONFIGS["CPU_CODEC"],
        FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["CPU_PRESET"],
        FFMPEG_COMMANDS.CONSTANT_RATE_FACTOR, FFMPEG_CONFIGS["CPU_CRF"],
        FFMPEG_COMMANDS.OVERWRITE_OUTPUT,
        output_path
    ]

def get_ffmpeg_pipe_cmd(
    width: int,
    height: int,
    fps: float,
    temp_watermark_path: str,
    input_video_path: str,
    use_cuda: bool,
    output_video_path: str,
    bitrate: str = None
) -> list[str]:

    # 1. Khai báo danh sách các cờ CQ/CRF cần loại bỏ nếu có bitrate
    remove_flags = set()
    if bitrate is not None:
        remove_flags = {
            getattr(FFMPEG_COMMANDS, "CQ_OPTION", None),
            FFMPEG_CONFIGS.get("CQ"),
            getattr(FFMPEG_COMMANDS, "CONSTANT_RATE_FACTOR", None),
            FFMPEG_CONFIGS.get("CPU_CRF")
        } - {None}
    """
    Build command list to push raw video frames to FFmpeg pipe.
    """
    if not FFMPEG_PATH:
        raise FileNotFoundError("FFmpeg executable not found. Please install it and add to your PATH.")
    # Base command
    cmd = [
        FFMPEG_PATH, FFMPEG_COMMANDS.OVERWRITE_OUTPUT,
        "-f", "rawvideo",
        FFMPEG_COMMANDS.PIXEL_FORMAT, FFMPEG_CONFIGS["RAW_PIX_FMT"],
        "-s", f"{width}x{height}",
        FFMPEG_COMMANDS.FRAME_RATE, f"{fps}",
        FFMPEG_COMMANDS.INPUT, "-", 
        FFMPEG_COMMANDS.INPUT, temp_watermark_path,
        FFMPEG_COMMANDS.INPUT, input_video_path,
        "-filter_complex", "[0:v][1:v]overlay=0:0[outv]",
        FFMPEG_COMMANDS.MAP, "[outv]",
        FFMPEG_COMMANDS.MAP, "2:a?",
    ]
    
    # Optional parameters can be added to the dictionary to support bitrate, QP, gop size
    # E.g., if FFMPEG_CONFIGS["GOP_SIZE"] is not None:
    #       cmd.extend(["-g", str(FFMPEG_CONFIGS["GOP_SIZE"])])
    
    if use_cuda:
        cmd.extend([
            FFMPEG_COMMANDS.VIDEO_CODEC, FFMPEG_CONFIGS["NVENC_H264_CODEC"],
            FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["NVENC_PRESET"],
            FFMPEG_COMMANDS.RC_OPTION, FFMPEG_CONFIGS["RC_VALUE"],
        ])
        if FFMPEG_CONFIGS["BITRATE"] is not None:
            cmd.extend(["-b:v", FFMPEG_CONFIGS["BITRATE"]])
        if FFMPEG_CONFIGS["CQ"] is not None:
            cmd.extend([FFMPEG_COMMANDS.CQ_OPTION, str(FFMPEG_CONFIGS["CQ"])])
        # if FFMPEG_CONFIGS["SCENECUT"] is not None:
        #     cmd.extend(["-no-scenecut", FFMPEG_CONFIGS["SCENECUT"]])
        if FFMPEG_CONFIGS["SPATIAL_VAL"] is not None: 
            cmd.extend([FFMPEG_COMMANDS.SPATIAL_AQ, str(FFMPEG_CONFIGS["SPATIAL_VAL"])])
        if FFMPEG_CONFIGS["TEMPORAL_VAL"] is not None: 
            cmd.extend([FFMPEG_COMMANDS.TEMPORAL_AQ, str(FFMPEG_CONFIGS["TEMPORAL_VAL"])])
        if FFMPEG_CONFIGS["MAX_MUTE_QUEUE_VAL"] is not None: 
            cmd.extend([FFMPEG_COMMANDS.MAX_MUTE_QUEUE, str(FFMPEG_CONFIGS["MAX_MUTE_QUEUE_VAL"])])
    else:
        cmd.extend([
            FFMPEG_COMMANDS.VIDEO_CODEC, FFMPEG_CONFIGS["CPU_CODEC"],
            FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["CPU_PRESET"],
            FFMPEG_COMMANDS.CONSTANT_RATE_FACTOR, FFMPEG_CONFIGS["CPU_CRF"],
            FFMPEG_COMMANDS.PIXEL_FORMAT, FFMPEG_CONFIGS["PIX_FMT"]
        ])

    if FFMPEG_CONFIGS["GOP_SIZE"] is not None:
        gop_size = int(FFMPEG_CONFIGS["GOP_SIZE"]) * 2
          # Set GOP size to 2 seconds worth of frames
        cmd.extend(["-g", str(gop_size)])

    final = [item for item in cmd if item not in remove_flags]

    if bitrate is not None:
        final.extend([FFMPEG_COMMANDS.VIDEO_BITRATE, str(bitrate)])
        
    final.append(output_video_path)
    return final

def get_ffmpeg_exact_cut_cmd(input_path: str, output_path: str, start_time: str, end_time: str) -> list[str]:
    """Build command for a precise, re-encoded cut."""
    if not FFMPEG_PATH:
        raise FileNotFoundError("FFmpeg executable not found. Please install it and add to your PATH.")
    return [
        FFMPEG_PATH,
        FFMPEG_COMMANDS.SEEK, start_time,
        FFMPEG_COMMANDS.INPUT, input_path,
        FFMPEG_COMMANDS.TO, end_time,
        FFMPEG_COMMANDS.VIDEO_FILTER, FFMPEG_FLAGS.SET_PTS_TO_START,
        FFMPEG_COMMANDS.AUDIO_FILTER, FFMPEG_FLAGS.ASET_PTS_TO_START,
        FFMPEG_COMMANDS.VIDEO_CODEC, FFMPEG_CONFIGS["CPU_CODEC"], # Re-encode for accuracy
        FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["CPU_PRESET"],
        FFMPEG_COMMANDS.CONSTANT_RATE_FACTOR, FFMPEG_CONFIGS["CPU_CRF"],
        FFMPEG_COMMANDS.AUDIO_CODEC, FFMPEG_CONFIGS["AUDIO_CODEC_AAC"], # Re-encode audio
        FFMPEG_COMMANDS.AUDIO_BITRATE, FFMPEG_CONFIGS["AUDIO_BITRATE_192K"],
        FFMPEG_COMMANDS.OVERWRITE_OUTPUT,
        output_path
    ]

def get_ffmpeg_snapshot_cmd(input_path: str, output_path: str, time: str, quality: int, format: str) -> list[str]:
    """Build command to take a single snapshot."""
    if not FFMPEG_PATH:
        raise FileNotFoundError("FFmpeg executable not found. Please install it and add to your PATH.")
    cmd = [
        FFMPEG_PATH,
        FFMPEG_COMMANDS.SEEK, time,
        FFMPEG_COMMANDS.INPUT, input_path,
        FFMPEG_COMMANDS.FRAMES_VIDEO, "1",
    ]
    if format.lower() == 'jpg':
        cmd.extend([FFMPEG_COMMANDS.QUALITY, str(quality)]) # Quality for JPG (1-31, lower is better)
    cmd.append(output_path)
    return cmd

def get_ffmpeg_crop_cmd(is_gpu = True, bitrate: str = None, filter_str: str = None) -> list[str]:
    # 1. Khai báo danh sách các cờ CQ/CRF cần loại bỏ nếu có bitrate
    remove_flags = set()
    if bitrate:
        remove_flags = {
            getattr(FFMPEG_COMMANDS, "CQ_OPTION", None),
            FFMPEG_CONFIGS.get("CQ"),
            getattr(FFMPEG_COMMANDS, "CONSTANT_RATE_FACTOR", None),
            FFMPEG_CONFIGS.get("CPU_CRF")
        } - {None}

    # Sửa lại thành:
    filter = filter_str if filter_str is not None else "crop={w}:{h}:{x}:{y}"
    # 2. Template CPU
    FFMPEG_CROP_CPU_CMD = [
        FFMPEG_PATH, FFMPEG_COMMANDS.OVERWRITE_OUTPUT,
        "-i", "{input_path}",
        FFMPEG_COMMANDS.VIDEO_FILTER_L, filter,
        FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["CPU_PRESET"],
        FFMPEG_COMMANDS.AUDIO_CODEC, "copy",
        FFMPEG_COMMANDS.VIDEO_CODEC, VIDEO_CODECS.CPU_H264,
        FFMPEG_COMMANDS.CONSTANT_RATE_FACTOR, FFMPEG_CONFIGS["CPU_CRF"],
        FFMPEG_COMMANDS.MAX_MUTE_QUEUE, FFMPEG_CONFIGS["MAX_MUTE_QUEUE_VAL"],
        "{output_path}"
    ]

    # 3. Template GPU (NVIDIA NVENC)
    FFMPEG_CROP_GPU_CMD = [
        FFMPEG_PATH, FFMPEG_COMMANDS.HARDWARE_ACCE, FFMPEG_CONFIGS["HWACCEL_CUDA"],
        FFMPEG_COMMANDS.OVERWRITE_OUTPUT,
        "-i", "{input_path}",
        FFMPEG_COMMANDS.VIDEO_FILTER_L, filter,
        FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["NVENC_PRESET"],
        FFMPEG_COMMANDS.AUDIO_CODEC, "copy",
        FFMPEG_COMMANDS.VIDEO_CODEC, VIDEO_CODECS.NVENC_H264,
        FFMPEG_COMMANDS.RC_OPTION, FFMPEG_CONFIGS["RC_VALUE"],
        FFMPEG_COMMANDS.MULTIPASS_OPTION , FFMPEG_CONFIGS["MULTIPASS_VAL"],
        FFMPEG_COMMANDS.CQ_OPTION, FFMPEG_CONFIGS["CQ"],
        FFMPEG_COMMANDS.SPATIAL_AQ, FFMPEG_CONFIGS["SPATIAL_VAL"],
        FFMPEG_COMMANDS.TEMPORAL_AQ, FFMPEG_CONFIGS["TEMPORAL_VAL"],
        FFMPEG_COMMANDS.MAX_MUTE_QUEUE, FFMPEG_CONFIGS["MAX_MUTE_QUEUE_VAL"],
        "{output_path}"
    ]

    # 4. Chọn template & Lọc bỏ cờ xung đột
    raw_cmd = FFMPEG_CROP_GPU_CMD if is_gpu else FFMPEG_CROP_CPU_CMD
    cmd = [item for item in raw_cmd if item not in remove_flags]

    # 5. Chèn "-b:v <bitrate>" vào trước "{output_path}"
    if bitrate:
        out_idx = cmd.index("{output_path}") if "{output_path}" in cmd else len(cmd) - 1
        cmd.insert(out_idx, "-b:v")
        cmd.insert(out_idx + 1, bitrate)

    return cmd


def get_ffmpeg_export_cmd(input_path: str, output_path: str, options: dict) -> list[str]:
    """Build command for exporting with various options (FPS, tracks, metadata)."""
    if not FFMPEG_PATH:
        raise FileNotFoundError("FFmpeg executable not found. Please install it and add to your PATH.")
    cmd = [FFMPEG_PATH, FFMPEG_COMMANDS.INPUT, input_path]

    # Video and Audio filters
    video_filters = []
    if options.get("fps"):
        video_filters.append(f'fps={options["fps"]}')

    if video_filters:
        cmd.extend(["-filter:v", ",".join(video_filters)])

    # Track handling
    if options.get('remove_audio'):
        cmd.append("-an")
    elif options.get('keep_audio', True):
        cmd.extend([FFMPEG_COMMANDS.MAP, "0:a?"])

    if options.get('remove_video'):
        cmd.append("-vn")
    elif options.get('keep_video', True):
        cmd.extend([FFMPEG_COMMANDS.MAP, "0:v?"])

    # Codec selection
    if not video_filters and not options.get('remove_audio') and not options.get('remove_video'):
        cmd.extend([FFMPEG_COMMANDS.COPY_CODEC, "copy"]) # Default to stream copy if no filters/track removal
    else:
        cmd.extend([FFMPEG_COMMANDS.VIDEO_CODEC, FFMPEG_CONFIGS["CPU_CODEC"], FFMPEG_COMMANDS.PRESET, FFMPEG_CONFIGS["CPU_PRESET"], FFMPEG_COMMANDS.CONSTANT_RATE_FACTOR, FFMPEG_CONFIGS["CPU_CRF"]])
        if not options.get('remove_audio'):
            cmd.extend([FFMPEG_COMMANDS.AUDIO_CODEC, FFMPEG_CONFIGS["AUDIO_CODEC_AAC"], FFMPEG_COMMANDS.AUDIO_BITRATE, FFMPEG_CONFIGS["AUDIO_BITRATE_192K"]]) # Re-encode audio if video is re-encoded

    # Metadata
    if options.get('metadata'):
        cmd.extend([FFMPEG_COMMANDS.MAP_METADATA, "-1"]) # Clear existing metadata
        for meta in options['metadata'].split('\n'):
            if '=' in meta:
                key, value = meta.split('=', 1)
                cmd.extend([FFMPEG_COMMANDS.METADATA, f'{key.strip()}={value.strip()}'])
    else:
        cmd.extend([FFMPEG_COMMANDS.MAP_METADATA, "0"]) # Keep original metadata

    cmd.extend([FFMPEG_COMMANDS.OVERWRITE_OUTPUT, output_path])
    return cmd
