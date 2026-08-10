import os
import unittest
import ffmpeg
from app.services import ffmpeg_service

class TestNewFeatures(unittest.TestCase):

    def setUp(self):
        self.video_path = "assets/demovideo.mp4"
        os.makedirs("assets", exist_ok=True)
        if not os.path.exists(self.video_path):
            try:
                (
                    ffmpeg
                    .input('testsrc=size=128x72:rate=10:duration=5', f='lavfi')
                    .output(self.video_path, pix_fmt='yuv420p')
                    .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
                )
            except ffmpeg.Error as e:
                self.fail(f"Failed to create test video: {e.stderr.decode()}")

    def test_get_video_fps(self):
        fps = ffmpeg_service.get_video_fps(self.video_path)
        self.assertGreater(fps, 0)

if __name__ == '__main__':
    unittest.main()
