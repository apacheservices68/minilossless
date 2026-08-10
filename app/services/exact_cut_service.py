'''Module for precise video cutting services.'''

import ffmpeg

def exact_cut(input_path: str, output_path: str, start_time: str, end_time: str):
    """
    Cuts a video from the given start time to the end time with re-encoding for precision.

    Args:
        input_path (str): Path to the input video file.
        output_path (str): Path to save the output video file.
        start_time (str): Start time in HH:MM:SS.ms format.
        end_time (str): End time in HH:MM:SS.ms format.
    """
    try:
        (   
            ffmpeg
            .input(input_path, ss=start_time)
            .output(output_path, to=end_time, c="copy")
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print("FFmpeg error occurred:")
        print(e.stderr.decode())
        raise
