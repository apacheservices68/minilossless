import pytest
from app.core.ffmpeg_config import get_ffmpeg_pipe_cmd, FFMPEG_CONFIGS

def test_get_ffmpeg_pipe_cmd_nvenc_cuda():
    """
    Test get_ffmpeg_pipe_cmd when use_cuda=True.
    Verify that the returned command is a list containing '-c:v h264_nvenc' and '-pix_fmt yuv420p'.
    """
    width = 1920
    height = 1080
    fps = 30.0
    temp_watermark_path = "temp_wm.png"
    input_video_path = "input.mp4"
    output_video_path = "output.mp4"
    
    cmd = get_ffmpeg_pipe_cmd(
        width=width,
        height=height,
        fps=fps,
        temp_watermark_path=temp_watermark_path,
        input_video_path=input_video_path,
        use_cuda=True,
        output_video_path=output_video_path
    )
    
    assert isinstance(cmd, list)
    
    # NVENC uses h264_nvenc and yuv420p as per FFMPEG_CONFIGS
    assert "-c:v" in cmd
    # Find the index of -c:v and assert the next element is h264_nvenc (or NVENC_CODEC)
    idx_codec = cmd.index("-c:v")
    assert cmd[idx_codec + 1] == FFMPEG_CONFIGS["NVENC_CODEC"]
    assert cmd[idx_codec + 1] == "h264_nvenc"
    
    assert "-pix_fmt" in cmd
    idx_pix_fmt = cmd.index("-pix_fmt")
    # There could be multiple -pix_fmt if rawvideo also specifies it, so let's verify yuv420p is one of the arguments or the trailing one.
    # Actually, let's make sure FFMPEG_CONFIGS["PIX_FMT"] (yuv420p) is present.
    assert FFMPEG_CONFIGS["PIX_FMT"] in cmd
    assert "yuv420p" in cmd
    
    # Check general properties
    assert "ffmpeg" in cmd
    assert input_video_path in cmd
    assert output_video_path in cmd
    assert temp_watermark_path in cmd

def test_get_ffmpeg_pipe_cmd_cpu():
    """
    Test get_ffmpeg_pipe_cmd when use_cuda=False.
    """
    width = 1920
    height = 1080
    fps = 30.0
    temp_watermark_path = "temp_wm.png"
    input_video_path = "input.mp4"
    output_video_path = "output.mp4"
    
    cmd = get_ffmpeg_pipe_cmd(
        width=width,
        height=height,
        fps=fps,
        temp_watermark_path=temp_watermark_path,
        input_video_path=input_video_path,
        use_cuda=False,
        output_video_path=output_video_path
    )
    
    assert isinstance(cmd, list)
    assert "-c:v" in cmd
    idx_codec = cmd.index("-c:v")
    assert cmd[idx_codec + 1] == FFMPEG_CONFIGS["CPU_CODEC"]
    assert cmd[idx_codec + 1] == "libx264"
    
    assert "yuv420p" in cmd
