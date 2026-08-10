
import unittest
from unittest.mock import patch, call
import ffmpeg

from app.services.exact_cut_service import exact_cut

class TestExactCutService(unittest.TestCase):

    @patch("ffmpeg.input")
    def test_exact_cut(self, mock_ffmpeg_input):
        """Test that exact_cut calls ffmpeg with the correct parameters."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_output = mock_stream.output
        mock_run = mock_output.return_value.run

        input_path = "dummy_input.mp4"
        output_path = "dummy_output.mp4"
        start_time = "00:01:23.456"
        end_time = "00:02:00.000"

        exact_cut(input_path, output_path, start_time, end_time)

        mock_ffmpeg_input.assert_called_with(input_path, ss=start_time)
        mock_output.assert_called_with(output_path, to=end_time, c="copy")
        mock_run.assert_called_with(overwrite_output=True, capture_stdout=True, capture_stderr=True)

    @patch("ffmpeg.input")
    def test_exact_cut_ffmpeg_error(self, mock_ffmpeg_input):
        """Test that exact_cut raises an exception when ffmpeg fails."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_output = mock_stream.output
        mock_run = mock_output.return_value.run
        mock_run.side_effect = ffmpeg.Error("ffmpeg", b"stdout", b"stderr")

        with self.assertRaises(ffmpeg.Error):
            exact_cut("in.mp4", "out.mp4", "0", "1")

if __name__ == '__main__':
    unittest.main()
