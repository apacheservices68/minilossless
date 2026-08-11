"""Module for precise video cutting services."""

import ffmpeg
import subprocess
from app.core.ffmpeg_resolver import get_ffmpeg_path

def exact_cut(input_path: str, output_path: str, start_time: str, duration: float, tracks: list = None):
    """
    Cuts a video from the given start time for a specific duration with re-encoding for precision.

    Args:
        input_path (str): Path to the input video file.
        output_path (str): Path to save the output video file.
        start_time (str): Start time in HH:MM:SS.ms format.
        duration (float): Duration of the cut in seconds.
        tracks (list): List of stream tracks to include.
    """
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        raise FileNotFoundError("ffmpeg executable not found.")

    cmd = [
        ffmpeg_path, "-y",
        "-ss", start_time,
        "-i", input_path,
        "-t", str(duration),
        "-vf", "setpts=PTS-STARTPTS",
        "-af", "asetpts=PTS-STARTPTS",
        "-pix_fmt", "yuv420p" # Ensure pixel format compatibility
    ]

    if tracks:
        map_flags = []
        metadata_flags = []
        output_stream_index = 0
        for track in tracks:
            if track.get("enabled", True):
                stream_index = track["index"]
                map_flags.extend(["-map", f"0:{stream_index}"])

                codec_type = track["codec_type"]
                if codec_type == "video":
                    cmd.extend([f"-c:v:{output_stream_index}", "libx264"])
                elif codec_type == "audio":
                    cmd.extend([f"-c:a:{output_stream_index}", "aac"])
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
            "-c:v", "libx264",
            "-c:a", "aac"
        ])

    cmd.append(output_path)

    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=True, 
            universal_newlines=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error occurred in exact_cut: {e.stderr}")
        raise Exception(e.stderr)
