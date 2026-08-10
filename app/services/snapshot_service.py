
"""Service for taking snapshots from a video."""
import ffmpeg
import os

def take_snapshot(input_path: str, output_path: str, timestamp_sec: float, quality: int, use_png: bool):
    """
    Takes a snapshot from a video at a specific timestamp.

    Args:
        input_path (str): Path to the input video file.
        output_path (str): Path to save the output snapshot.
        timestamp_sec (float): The timestamp in seconds to capture.
        quality (int): Quality from 1 to 100. Higher is better.
        use_png (bool): If True, saves as PNG; otherwise, saves as JPG.
    """
    try:
        stream = ffmpeg.input(input_path, ss=timestamp_sec)
        
        if use_png:
            stream = stream.output(output_path, vframes=1, format='image2', vcodec='png')
        else:
            qscale = round(31 - (quality - 1) * 30 / 99)
            if qscale < 1: qscale = 1
            if qscale > 31: qscale = 31
            
            stream = stream.output(output_path, vframes=1, format='image2', vcodec='mjpeg', q=qscale)

        stream.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)

    except ffmpeg.Error as e:
        print(f"FFmpeg error taking snapshot: {e.stderr.decode()}")
        raise

