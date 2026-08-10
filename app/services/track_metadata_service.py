
"""Module for handling video/audio tracks and metadata."""

from typing import Dict
import ffmpeg

def remove_audio(input_path: str, output_path: str):
    """Removes the audio track from a video.

    Args:
        input_path (str): Path to the input file.
        output_path (str): Path to the output file.
    """
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, an=None, c="copy")
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(f"FFmpeg error removing audio: {e.stderr.decode()}")
        raise

def remove_video(input_path: str, output_path: str):
    """Removes the video track from a file.

    Args:
        input_path (str): Path to the input file.
        output_path (str): Path to the output file.
    """
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vn=None, c="copy")
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(f"FFmpeg error removing video: {e.stderr.decode()}")
        raise

def set_metadata(input_path: str, output_path: str, metadata: Dict[str, str]):
    """Sets metadata for a media file.

    Args:
        input_path (str): Path to the input file.
        output_path (str): Path to the output file.
        metadata (Dict[str, str]): Dictionary of metadata keys and values.
    """
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, metadata=metadata, c="copy")
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(f"FFmpeg error setting metadata: {e.stderr.decode()}")
        raise

def clear_metadata(input_path: str, output_path: str):
    """Removes all metadata from a media file.

    Args:
        input_path (str): Path to the input file.
        output_path (str): Path to the output file.
    """
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, map_metadata=-1, c="copy")
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(f"FFmpeg error clearing metadata: {e.stderr.decode()}")
        raise

def get_metadata(input_path: str) -> Dict:
    """Retrieves metadata from a media file.

    Args:
        input_path (str): Path to the input file.

    Returns:
        Dict: A dictionary containing file format and stream information.
    """
    try:
        probe = ffmpeg.probe(input_path)
        return probe
    except ffmpeg.Error as e:
        print(f"FFmpeg error probing file: {e.stderr.decode()}")
        raise
