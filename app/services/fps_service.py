
"""Module for handling video FPS (Frames Per Second)."""

import ffmpeg

def get_fps(input_path: str) -> float:
    """
    Gets the FPS of a video file.

    Args:
        input_path (str): Path to the input video file.

    Returns:
        float: The frames per second of the video.
    """
    try:
        probe = ffmpeg.probe(input_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream and 'avg_frame_rate' in video_stream and video_stream['avg_frame_rate'] != '0/0':
            num, den = map(int, video_stream['avg_frame_rate'].split('/'))
            return num / den
        return 0.0
    except ffmpeg.Error as e:
        print(f"FFmpeg error probing file: {input_path}")
        print(e.stderr.decode())
        raise

def change_fps(input_path: str, output_path: str, fps: float):
    """
    Changes the FPS of a video using a filter.

    Args:
        input_path (str): Path to the input video file.
        output_path (str): Path to the output video file.
        fps (float): The target FPS.
    """
    try:
        (
            ffmpeg
            .input(input_path)
            .filter('fps', fps=fps)
            .output(output_path)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print("FFmpeg error occurred:")
        print(e.stderr.decode())
        raise
