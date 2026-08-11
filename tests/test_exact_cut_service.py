'''
import unittest
from unittest.mock import patch, MagicMock
import subprocess

from app.services.exact_cut_service import exact_cut

class TestExactCutService(unittest.TestCase):

    @patch("app.services.exact_cut_service.get_ffmpeg_path")
    @patch("subprocess.run")
    def test_exact_cut(self, mock_subprocess_run, mock_get_ffmpeg_path):
        """Test that exact_cut calls ffmpeg with the correct parameters."""
        mock_get_ffmpeg_path.return_value = "/fake/ffmpeg"
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        input_path = "dummy_input.mp4"
        output_path = "dummy_output.mp4"
        start_time = "00:01:23.456"
        duration = 120.0

        exact_cut(input_path, output_path, start_time, duration)

        expected_cmd = [
            '/fake/ffmpeg', '-y', '-ss', '00:01:23.456', '-i', 'dummy_input.mp4',
            '-t', '120.0', '-vf', 'setpts=PTS-STARTPTS', '-af', 'asetpts=PTS-STARTPTS',
            '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-c:a', 'aac', 'dummy_output.mp4'
        ]

        mock_subprocess_run.assert_called_once_with(
            expected_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            universal_newlines=True
        )

    @patch("app.services.exact_cut_service.get_ffmpeg_path")
    @patch("subprocess.run")
    def test_exact_cut_ffmpeg_error(self, mock_subprocess_run, mock_get_ffmpeg_path):
        """Test that exact_cut raises an exception when ffmpeg fails."""
        mock_get_ffmpeg_path.return_value = "/fake/ffmpeg"
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="ffmpeg error")

        with self.assertRaises(Exception) as context:
            exact_cut("in.mp4", "out.mp4", "0", 1.0)
        
        self.assertIn("ffmpeg error", str(context.exception))

    @patch("app.services.exact_cut_service.get_ffmpeg_path")
    @patch("subprocess.run")
    def test_exact_cut_with_float_duration(self, mock_subprocess_run, mock_get_ffmpeg_path):
        """Test that exact_cut formats float duration correctly."""
        mock_get_ffmpeg_path.return_value = "/fake/ffmpeg"
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        exact_cut("in.mp4", "out.mp4", "00:00:00", 2.3)

        called_cmd = mock_subprocess_run.call_args[0][0]
        self.assertIn("-t", called_cmd)
        t_index = called_cmd.index("-t")
        self.assertEqual(called_cmd[t_index + 1], "2.300")

if __name__ == '__main__':
    unittest.main()
'''
