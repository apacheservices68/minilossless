import sys
import unittest
from unittest.mock import patch, MagicMock, call
import os

# Cần mock QApplication để khởi tạo widget
from PyQt6.QtWidgets import QApplication

# Đối tượng cần test
from app.ui.main_window import BasicCutTab, MainWindow

# Đường dẫn để patch
FFMPEG_SERVICE_PATH = 'app.services.ffmpeg_service'
MAIN_WINDOW_UI_PATH = 'app.ui.main_window'
OS_PATH = 'os'

# Khởi tạo một QApplication instance, cần thiết cho mọi ứng dụng PyQt
# Thậm chí khi chạy test mà không có giao diện đồ họa thực tế.
app = QApplication(sys.argv)

class TestExportModes(unittest.TestCase):

    def setUp(self):
        """Hàm này được chạy trước mỗi test case."""
        # Bắt đầu các patcher để chúng có thể được truy cập trong tất cả các test
        self.patcher_get_dir = patch(f'{MAIN_WINDOW_UI_PATH}.QFileDialog.getExistingDirectory')
        self.patcher_msg_box = patch(f'{MAIN_WINDOW_UI_PATH}.QMessageBox')

        self.mock_get_dir = self.patcher_get_dir.start()
        self.mock_msg_box = self.patcher_msg_box.start()

        # Thiết lập mock cho QFileDialog để luôn trả về một đường dẫn giả
        self.mock_output_dir = '/fake/output/dir'
        self.mock_get_dir.return_value = self.mock_output_dir

        # Khởi tạo MainWindow và BasicCutTab
        with patch(f'{MAIN_WINDOW_UI_PATH}.MainWindow.init_ui', MagicMock()):
            self.main_window = MainWindow()

        self.main_window.selected_video_path = '/fake/video.mp4'
        self.main_window.log = MagicMock() # Mock hàm log để tránh lỗi

        # Khởi tạo BasicCutTab, truyền main_window đã mock vào
        with patch(f'{MAIN_WINDOW_UI_PATH}.BasicCutTab.init_ui', MagicMock()):
            self.basic_tab = BasicCutTab(self.main_window)
            self.basic_tab.segments_widget = MagicMock()
            self.basic_tab.segments_widget.cb_export_mode = MagicMock()
            self.basic_tab.segments_widget.chk_cleanup = MagicMock()
            self.basic_tab.track_control_widget = MagicMock()
            self.basic_tab.track_control_widget.is_audio_discarded = False

    def tearDown(self):
        """Chạy sau mỗi test case để dọn dẹp."""
        self.patcher_get_dir.stop()
        self.patcher_msg_box.stop()

    @patch(f'{FFMPEG_SERVICE_PATH}.cut_video')
    @patch(f'{FFMPEG_SERVICE_PATH}.merge_videos')
    @patch(f'{OS_PATH}.remove')
    def test_export_separate_files_mode(self, mock_os_remove, mock_merge_videos, mock_cut_video):
        """Kiểm tra chế độ 'Separate files': Chỉ xuất các file segment, không merge, không xóa."""
        # --- Setup --- #
        self.basic_tab.segments = [
            {'start': 10.5, 'end': 20.0},
            {'start': 30.0, 'end': 40.2}
        ]
        self.basic_tab.segments_widget.cb_export_mode.currentData.return_value = 'separate'
        self.basic_tab.segments_widget.chk_cleanup.isChecked.return_value = False

        # --- Thực thi --- #
        self.basic_tab.export_segments_action()

        # --- Khẳng định --- #
        self.assertEqual(mock_cut_video.call_count, 2)
        expected_calls = [
            call("/fake/video.mp4", os.path.join(self.mock_output_dir, "video_00-00-10_00-00-20.mp4"), "00:00:10", "00:00:20", tracks=self.basic_tab.track_control_widget.tracks, audio_codec="copy"),
            call("/fake/video.mp4", os.path.join(self.mock_output_dir, "video_00-00-30_00-00-40.mp4"), "00:00:30", "00:00:40", tracks=self.basic_tab.track_control_widget.tracks, audio_codec="copy"),
        ]
        mock_cut_video.assert_has_calls(expected_calls, any_order=True)

    @patch(f'{FFMPEG_SERVICE_PATH}.cut_video')
    @patch(f'{FFMPEG_SERVICE_PATH}.merge_videos')
    @patch(f'{OS_PATH}.remove')
    def test_export_with_discard_audio(self, mock_os_remove, mock_merge_videos, mock_cut_video):
        """Kiểm tra export với tùy chọn Discard Audio."""
        # --- Setup --- #
        self.basic_tab.segments = [
            {'start': 1.0, 'end': 2.0},
        ]
        self.basic_tab.segments_widget.cb_export_mode.currentData.return_value = 'separate'
        self.basic_tab.track_control_widget.is_audio_discarded = True

        # --- Thực thi --- #
        self.basic_tab.export_segments_action()

        # --- Khẳng định --- #
        mock_cut_video.assert_called_once_with(
            '/fake/video.mp4',
            os.path.join(self.mock_output_dir, 'video_00-00-01_00-00-02.mp4'),
            '00:00:01',
            '00:00:02',
            tracks=self.basic_tab.track_control_widget.tracks,
            audio_codec=None
        )

        mock_merge_videos.assert_not_called()
        mock_os_remove.assert_not_called()
        self.main_window.log.assert_any_call("Starting export with mode: separate")

    @patch(f'{FFMPEG_SERVICE_PATH}.cut_video')
    @patch(f'{FFMPEG_SERVICE_PATH}.merge_videos')
    @patch(f'{OS_PATH}.remove')
    def test_export_merge_mode_no_cleanup(self, mock_os_remove, mock_merge_videos, mock_cut_video):
        """Kiểm tra 'Merge': Xuất, merge, nhưng không xóa file tạm."""
        # --- Setup --- #
        self.basic_tab.segments = [
            {'start': 5.0, 'end': 8.0}
        ]
        self.basic_tab.segments_widget.cb_export_mode.currentData.return_value = 'merge'
        self.basic_tab.segments_widget.chk_cleanup.isChecked.return_value = False

        mock_cut_video.return_value = None

        # --- Thực thi --- #
        self.basic_tab.export_segments_action()

        # --- Khẳng định --- #
        mock_cut_video.assert_called_once()
        
        exported_file = os.path.join(self.mock_output_dir, 'video_00-00-05_00-00-08.mp4')
        merged_file = os.path.join(self.mock_output_dir, 'video_merged.mp4')

        mock_cut_video.assert_called_with("/fake/video.mp4", exported_file, "00:00:05", "00:00:08", tracks=self.basic_tab.track_control_widget.tracks, audio_codec="copy")
        mock_merge_videos.assert_called_once_with([exported_file], merged_file)
        mock_os_remove.assert_not_called()
        self.main_window.log.assert_any_call("Starting export with mode: merge")
        self.main_window.log.assert_any_call(f"Merging 1 files into video_merged.mp4...")

    @patch(f'{FFMPEG_SERVICE_PATH}.cut_video')
    @patch(f'{FFMPEG_SERVICE_PATH}.merge_videos')
    @patch(f'{OS_PATH}.remove')
    def test_export_merge_mode_with_cleanup(self, mock_os_remove, mock_merge_videos, mock_cut_video):
        """Kiểm tra 'Merge': Xuất, merge, và xóa file tạm."""
        # --- Setup --- #
        self.basic_tab.segments = [
            {'start': 1.0, 'end': 2.0},
            {'start': 3.0, 'end': 4.0}
        ]
        self.basic_tab.segments_widget.cb_export_mode.currentData.return_value = 'merge'
        self.basic_tab.segments_widget.chk_cleanup.isChecked.return_value = True

        mock_cut_video.return_value = None

        # --- Thực thi --- #
        self.basic_tab.export_segments_action()

        # --- Khẳng định --- #
        self.assertEqual(mock_cut_video.call_count, 2)
        
        exported_file1 = os.path.join(self.mock_output_dir, 'video_00-00-01_00-00-02.mp4')
        exported_file2 = os.path.join(self.mock_output_dir, 'video_00-00-03_00-00-04.mp4')
        merged_file = os.path.join(self.mock_output_dir, 'video_merged.mp4')

        mock_merge_videos.assert_called_once_with([exported_file1, exported_file2], merged_file)
        mock_cut_video.assert_has_calls([
            call("/fake/video.mp4", exported_file1, "00:00:01", "00:00:02", tracks=self.basic_tab.track_control_widget.tracks, audio_codec="copy"),
            call("/fake/video.mp4", exported_file2, "00:00:03", "00:00:04", tracks=self.basic_tab.track_control_widget.tracks, audio_codec="copy"),
        ], any_order=True)
        
        self.assertEqual(mock_os_remove.call_count, 2)
        mock_os_remove.assert_has_calls([call(exported_file1), call(exported_file2)], any_order=True)
        self.main_window.log.assert_any_call("Cleaning up intermediate segment files...")

    @patch(f'{FFMPEG_SERVICE_PATH}.cut_video')
    def test_export_stops_if_no_segments(self, mock_cut_video):
        """Kiểm tra việc export không chạy nếu không có segments."""
        # --- Setup --- #
        self.basic_tab.segments = [] # No segments
        
        # --- Thực thi --- #
        self.basic_tab.export_segments_action()
        
        # --- Khẳng định --- #
        mock_cut_video.assert_not_called()
        self.main_window.log.assert_not_called()

        # Kiểm tra xem QMessageBox.warning có được gọi không
        self.mock_msg_box.warning.assert_called_once()



if __name__ == '__main__':
    unittest.main()



