
import os
import unittest
from app.services import snapshot_service
import ffmpeg

class TestSnapshotService(unittest.TestCase):

    def setUp(self):
        self.video_path = "test_video.mp4"
        # Create a dummy video file for testing
        try:
            (
                ffmpeg
                .input('testsrc=size=128x72:rate=1:duration=5', f='lavfi')
                .output(self.video_path, pix_fmt='yuv420p') # yuv420p is a widely compatible pixel format
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            self.fail(f"Failed to create test video: {e.stderr.decode()}")

        self.output_jpg = "test_snapshot.jpg"
        self.output_png = "test_snapshot.png"

    def tearDown(self):
        if os.path.exists(self.video_path):
            os.remove(self.video_path)
        if os.path.exists(self.output_jpg):
            os.remove(self.output_jpg)
        if os.path.exists(self.output_png):
            os.remove(self.output_png)

    def test_take_snapshot_jpg(self):
        snapshot_service.take_snapshot(self.video_path, self.output_jpg, timestamp_sec=1.0, quality=80, use_png=False)
        self.assertTrue(os.path.exists(self.output_jpg))

    def test_take_snapshot_png(self):
        snapshot_service.take_snapshot(self.video_path, self.output_png, timestamp_sec=1.0, quality=80, use_png=True)
        self.assertTrue(os.path.exists(self.output_png))

if __name__ == '__main__':
    unittest.main()
