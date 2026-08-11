
import pytest
from unittest.mock import patch, MagicMock
from app.services.ffmpeg_service import cut_video
from app.services.exact_cut_service import exact_cut

@pytest.fixture
def mock_subprocess_run():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        yield mock_run

def test_lossless_cut_invokes_correct_command(mock_subprocess_run):
    cut_video(
        'input.mp4', 'output.mp4', '00:01:00', '00:02:00', 
        duration=60.0, is_smart_cut=False
    )
    mock_subprocess_run.assert_called_once()
    cmd = mock_subprocess_run.call_args[0][0]
    assert 'setpts=PTS-STARTPTS' not in ' '.join(cmd)
    assert '-c' in cmd
    assert 'copy' in cmd

@patch('app.services.ffmpeg_service.exact_cut_video')
def test_cut_video_routes_to_smart_cut(mock_exact_cut):
    cut_video(
        'input.mp4', 'output.mp4', '00:01:00', '00:02:00', 
        duration=60.0, is_smart_cut=True, tracks=[]
    )
    mock_exact_cut.assert_called_once_with(
        'input.mp4', 'output.mp4', '00:01:00', 60.0, []
    )

def test_smart_cut_invokes_correct_command(mock_subprocess_run):
    exact_cut(
        'input.mp4', 'output.mp4', '00:01:00', duration=5.0
    )
    mock_subprocess_run.assert_called_once()
    cmd = mock_subprocess_run.call_args[0][0]
    cmd_str = ' '.join(cmd)
    
    assert '-ss 00:01:00' in cmd_str
    assert '-t 5.0' in cmd_str
    assert '-vf setpts=PTS-STARTPTS' in cmd_str
    assert '-af asetpts=PTS-STARTPTS' in cmd_str
    assert 'libx264' in cmd_str
    assert 'aac' in cmd_str
