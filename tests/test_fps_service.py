
import unittest
from unittest.mock import patch
import ffmpeg

from app.services.fps_service import get_fps, change_fps

class TestFpsService(unittest.TestCase):

    @patch("ffmpeg.probe")
    def test_get_fps(self, mock_ffmpeg_probe):
        """Test that get_fps correctly parses the probe output."""
        mock_ffmpeg_probe.return_value = {
            "streams": [
                {
                    "codec_type": "video",
                    "avg_frame_rate": "30000/1001"
                },
                {
                    "codec_type": "audio"
                }
            ]
        }

        fps = get_fps("dummy_input.mp4")
        self.assertAlmostEqual(fps, 29.97, places=2)
    
    @patch("ffmpeg.probe")
    def test_get_fps_no_video_stream(self, mock_ffmpeg_probe):
        """Test get_fps with no video stream."""
        mock_ffmpeg_probe.return_value = {
            "streams": [
                {
                    "codec_type": "audio"
                }
            ]
        }
        fps = get_fps("dummy_audio.mp3")
        self.assertEqual(fps, 0.0)


    @patch("ffmpeg.input")
    def test_change_fps(self, mock_ffmpeg_input):
        """Test that change_fps calls ffmpeg with the correct filter."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_filter = mock_stream.filter
        mock_output = mock_filter.return_value.output
        mock_run = mock_output.return_value.run

        change_fps("input.mp4", "output.mp4", 25)

        mock_ffmpeg_input.assert_called_with("input.mp4")
        mock_filter.assert_called_with("fps", fps=25)
        mock_output.assert_called_with("output.mp4")
        mock_run.assert_called_with(overwrite_output=True, capture_stdout=True, capture_stderr=True)

    @patch("ffmpeg.input")
    def test_change_fps_ffmpeg_error(self, mock_ffmpeg_input):
        """Test that change_fps raises an exception when ffmpeg fails."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_filter = mock_stream.filter
        mock_output = mock_filter.return_value.output
        mock_run = mock_output.return_value.run
        mock_run.side_effect = ffmpeg.Error("ffmpeg", b"stdout", b"stderr")

        with self.assertRaises(ffmpeg.Error):
            change_fps("in.mp4", "out.mp4", 30)


if __name__ == '__main__':
    unittest.main()
