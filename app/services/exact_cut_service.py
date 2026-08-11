"""Module for precise video cutting services."""

import ffmpeg
import subprocess
from app.core.ffmpeg_resolver import get_ffmpeg_path
from app.core.constants import FFMPEG_COMMANDS, FFMPEG_FLAGS, PIXEL_FORMATS, VIDEO_CODECS

def exact_cut(input_path: str, output_path: str, start_time: str, duration: float, tracks: list = None, progress_callback=None):
    """
    Cuts a video from the given start time for a specific duration with re-encoding for precision.

    Args:
        input_path (str): Path to the input video file.
        output_path (str): Path to save the output video file.
        start_time (str): Start time in HH:MM:SS.ms format.
        duration (float): Duration of the cut in seconds.
        tracks (list): List of stream tracks to include.
        progress_callback (function): Callback for progress updates.
    """
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        raise FileNotFoundError("ffmpeg executable not found.")
    
    if progress_callback:
        progress_callback("keyframe", 33)

    cmd = [
        ffmpeg_path, FFMPEG_COMMANDS.OVERWRITE_OUTPUT,
        FFMPEG_COMMANDS.SEEK, start_time,
        FFMPEG_COMMANDS.INPUT, input_path,
        "-t", f"{duration:.3f}",
        FFMPEG_COMMANDS.VIDEO_FILTER, FFMPEG_FLAGS.SET_PTS_TO_START,
        FFMPEG_COMMANDS.AUDIO_FILTER, FFMPEG_FLAGS.ASET_PTS_TO_START,
        FFMPEG_COMMANDS.PIXEL_FORMAT, PIXEL_FORMATS.YUV420P # Ensure pixel format compatibility
    ]

    if tracks:
        map_flags = []
        metadata_flags = []
        output_stream_index = 0
        for track in tracks:
            if track.get("enabled", True):
                stream_index = track["index"]
                map_flags.extend([FFMPEG_COMMANDS.MAP, f"0:{stream_index}"])

                codec_type = track["codec_type"]
                if codec_type == "video":
                    cmd.extend([f"{FFMPEG_COMMANDS.VIDEO_CODEC}:{output_stream_index}", VIDEO_CODECS.CPU_H264])
                elif codec_type == "audio":
                    cmd.extend([f"{FFMPEG_COMMANDS.AUDIO_CODEC}:{output_stream_index}", VIDEO_CODECS.AAC])
                else:
                    cmd.extend([f"-c:{output_stream_index}", "copy"]) # Copy other streams like subtitles

                if "tags" in track:
                    for key, value in track["tags"].items():
                        metadata_flags.extend([f"-metadata:s:{output_stream_index}", f"{key}={value}"])
                output_stream_index += 1
        cmd.extend(map_flags)
        cmd.extend(metadata_flags)
    else:
        # Default to re-encoding video with libx264 and copying audio
        cmd.extend([
            FFMPEG_COMMANDS.VIDEO_CODEC, VIDEO_CODECS.CPU_H264,
            FFMPEG_COMMANDS.AUDIO_CODEC, VIDEO_CODECS.AAC
        ])

    cmd.append(output_path)

    try:
        if progress_callback:
            progress_callback("re-encoding", 66)

        # Using capture_output=True is a more modern equivalent for PIPE
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True
        )

        if progress_callback:
            progress_callback("cutting", 100)

        return True
    except subprocess.CalledProcessError as e:
        error_message = f"FFmpeg exact_cut failed with return code {e.returncode}.\nOutput:\n{e.stdout}\nError:\n{e.stderr}"
        print(error_message)
        raise Exception(error_message)
    except FileNotFoundError as e:
        error_message = f"ffmpeg command not found: {e}. Ensure ffmpeg is in your system's PATH."
        print(error_message)
        raise Exception(error_message)
    except Exception as e:
        error_message = f"An unexpected error occurred during exact_cut: {e}"
        print(error_message)
        raise Exception(error_message)
