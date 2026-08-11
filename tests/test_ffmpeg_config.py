import pytest
from app.core.ffmpeg_config import (
    get_ffmpeg_cut_cmd,
    get_ffmpeg_merge_cmd,
    get_ffmpeg_watermark_cmd,
    get_ffmpeg_pipe_cmd,
    get_ffmpeg_exact_cut_cmd,
    get_ffmpeg_snapshot_cmd,
    get_ffmpeg_export_cmd,
    FFMPEG_CONFIGS
)
from app.core.constants import FFMPEG_COMMANDS, FFMPEG_FLAGS, PIXEL_FORMATS, VIDEO_CODECS, HW_ACCELS

def test_get_ffmpeg_pipe_cmd_nvenc_cuda():
    width, height, fps = 1920, 1080, 30.0
    temp_watermark_path, input_video_path, output_video_path = "temp_wm.png", "input.mp4", "output.mp4"

    cmd = get_ffmpeg_pipe_cmd(width, height, fps, temp_watermark_path, input_video_path, True, output_video_path)

    assert isinstance(cmd, list)
    assert FFMPEG_COMMANDS.VIDEO_CODEC in cmd
    idx_codec = cmd.index(FFMPEG_COMMANDS.VIDEO_CODEC)
    assert cmd[idx_codec + 1] == FFMPEG_CONFIGS["NVENC_H264_CODEC"]
    # The pix_fmt is not explicitly set for NVENC in the command builder
    assert FFMPEG_CONFIGS["PIX_FMT"] not in cmd

def test_get_ffmpeg_pipe_cmd_cpu():
    width, height, fps = 1920, 1080, 30.0
    temp_watermark_path, input_video_path, output_video_path = "temp_wm.png", "input.mp4", "output.mp4"

    cmd = get_ffmpeg_pipe_cmd(width, height, fps, temp_watermark_path, input_video_path, False, output_video_path)

    assert isinstance(cmd, list)
    assert FFMPEG_COMMANDS.VIDEO_CODEC in cmd
    idx_codec = cmd.index(FFMPEG_COMMANDS.VIDEO_CODEC)
    assert cmd[idx_codec + 1] == FFMPEG_CONFIGS["CPU_CODEC"]
    assert FFMPEG_CONFIGS["PIX_FMT"] in cmd

def test_ffmpeg_configs_values():
    assert FFMPEG_CONFIGS["CPU_CODEC"] == VIDEO_CODECS.CPU_H264
    assert FFMPEG_CONFIGS["NVENC_H264_CODEC"] == VIDEO_CODECS.NVENC_H264
    assert FFMPEG_CONFIGS["PIX_FMT"] == PIXEL_FORMATS.YUV420P
    assert FFMPEG_CONFIGS["HWACCEL_CUDA"] == HW_ACCELS.CUDA
