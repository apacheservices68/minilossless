
import unittest
from unittest.mock import patch
import ffmpeg

from app.services.track_metadata_service import (
    remove_audio,
    remove_video,
    set_metadata,
    clear_metadata,
    get_metadata
)

class TestTrackMetadataService(unittest.TestCase):

    @patch("ffmpeg.input")
    def test_remove_audio(self, mock_ffmpeg_input):
        """Test that remove_audio calls ffmpeg with the -an flag."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_output = mock_stream.output
        mock_run = mock_output.return_value.run

        remove_audio("input.mp4", "output.mp4")

        mock_ffmpeg_input.assert_called_with("input.mp4")
        mock_output.assert_called_with("output.mp4", an=None, c="copy")
        mock_run.assert_called_with(overwrite_output=True, capture_stdout=True, capture_stderr=True)

    @patch("ffmpeg.input")
    def test_remove_video(self, mock_ffmpeg_input):
        """Test that remove_video calls ffmpeg with the -vn flag."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_output = mock_stream.output
        mock_run = mock_output.return_value.run

        remove_video("input.mp4", "output.mp3")
        
        mock_ffmpeg_input.assert_called_with("input.mp4")
        mock_output.assert_called_with("output.mp3", vn=None, c="copy")
        mock_run.assert_called_with(overwrite_output=True, capture_stdout=True, capture_stderr=True)

    @patch("ffmpeg.input")
    def test_set_metadata(self, mock_ffmpeg_input):
        """Test that set_metadata calls ffmpeg with the correct metadata flags."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_output = mock_stream.output
        mock_run = mock_output.return_value.run

        metadata = {"title": "My Video", "artist": "My Self"}
        set_metadata("input.mp4", "output.mp4", metadata)

        mock_ffmpeg_input.assert_called_with("input.mp4")
        mock_output.assert_called_with("output.mp4", metadata=metadata, c="copy")
        mock_run.assert_called_with(overwrite_output=True, capture_stdout=True, capture_stderr=True)

    @patch("ffmpeg.input")
    def test_clear_metadata(self, mock_ffmpeg_input):
        """Test that clear_metadata calls ffmpeg with the -map_metadata -1 flag."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_output = mock_stream.output
        mock_run = mock_output.return_value.run

        clear_metadata("input.mp4", "output.mp4")

        mock_ffmpeg_input.assert_called_with("input.mp4")
        mock_output.assert_called_with("output.mp4", map_metadata=-1, c="copy")
        mock_run.assert_called_with(overwrite_output=True, capture_stdout=True, capture_stderr=True)

    @patch("ffmpeg.input")
    def test_ffmpeg_errors(self, mock_ffmpeg_input):
        """Test that all functions raise an exception when ffmpeg fails."""
        mock_stream = mock_ffmpeg_input.return_value
        mock_output = mock_stream.output
        mock_run = mock_output.return_value.run
        mock_run.side_effect = ffmpeg.Error("ffmpeg", b"stdout", b"stderr")

        with self.assertRaises(ffmpeg.Error):
            remove_audio("in.mp4", "out.mp4")
        with self.assertRaises(ffmpeg.Error):
            remove_video("in.mp4", "out.mp4")
        with self.assertRaises(ffmpeg.Error):
            set_metadata("in.mp4", "out.mp4", {})
        with self.assertRaises(ffmpeg.Error):
            clear_metadata("in.mp4", "out.mp4")

    @patch("ffmpeg.probe")
    def test_get_metadata(self, mock_ffmpeg_probe):
        """Test that get_metadata calls ffmpeg.probe and returns the result."""
        mock_ffmpeg_probe.return_value = {"format": {"tags": {"title": "test"}}}

        metadata = get_metadata("input.mp4")

        mock_ffmpeg_probe.assert_called_with("input.mp4")
        self.assertEqual(metadata, {"format": {"tags": {"title": "test"}}})

if __name__ == '__main__':
    unittest.main()
