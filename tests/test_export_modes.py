
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
        # Bắt đầu các patcher
        self.patcher_get_dir = patch(f'{MAIN_WINDOW_UI_PATH}.QFileDialog.getExistingDirectory')
        self.patcher_msg_box = patch(f'{MAIN_WINDOW_UI_PATH}.QMessageBox')
        self.patcher_cut_video = patch(f'{FFMPEG_SERVICE_PATH}.cut_video')
        self.patcher_merge_videos = patch(f'{FFMPEG_SERVICE_PATH}.merge_videos')
        self.patcher_os_remove = patch(f'{MAIN_WINDOW_UI_PATH}.os.remove')

        self.mock_get_dir = self.patcher_get_dir.start()
        self.mock_msg_box = self.patcher_msg_box.start()
        self.mock_cut_video = self.patcher_cut_video.start()
        self.mock_merge_videos = self.patcher_merge_videos.start()
        self.mock_os_remove = self.patcher_os_remove.start()

        # Thiết lập mock cho QFileDialog để luôn trả về một đường dẫn giả
        self.mock_output_dir = '/fake/output/dir'
        self.mock_get_dir.return_value = self.mock_output_dir

        # Khởi tạo MainWindow và BasicCutTab
        with patch(f'{MAIN_WINDOW_UI_PATH}.MainWindow.init_ui', MagicMock()):
            self.main_window = MainWindow()

        self.main_window.selected_video_path = '/fake/video.mp4'
        self.main_window.log = MagicMock() # Mock hàm log để tránh lỗi

        # Khởi tạo BasicCutTab
        with patch(f'{MAIN_WINDOW_UI_PATH}.BasicCutTab.init_ui', MagicMock()):
            self.basic_tab = BasicCutTab(self.main_window)
            self.basic_tab.segments_widget = MagicMock()
            self.basic_tab.segments_widget.cb_export_mode = MagicMock()
            self.basic_tab.segments_widget.chk_cleanup = MagicMock()
            self.basic_tab.segments_widget.smart_cut_checkbox = MagicMock()
            self.basic_tab.track_control_widget = MagicMock()
            self.basic_tab.track_control_widget.is_audio_discarded = False
            self.basic_tab.track_control_widget.tracks = [{'id': 1, 'codec_type': 'video'}] # Mock tracks
            self.basic_tab.segments_widget.smart_cut_checkbox.isChecked.return_value = False # Default to not smart cut

    def tearDown(self):
        """Chạy sau mỗi test case để dọn dẹp."""
        patch.stopall()

    def test_export_separate_files_mode(self):
        """Kiểm tra chế độ export 'Separate files'."""
        # --- Setup --- #
        self.basic_tab.segments = [
            {'start': 10.5, 'end': 20.0},
            {'start': 30.0, 'end': 40.2}
        ]
        self.basic_tab.segments_widget.cb_export_mode.currentData.return_value = 'separate'
        self.basic_tab.segments_widget.smart_cut_checkbox.isChecked.return_value = False

        # --- Thực thi --- #
        self.basic_tab.export_segments_action()

        # --- Khẳng định --- #
        self.assertEqual(self.mock_cut_video.call_count, 2)
        
        # Kiểm tra call đầu tiên
        self.mock_cut_video.assert_any_call(
            '/fake/video.mp4',
            unittest.mock.ANY,
            '00:00:10.500', 
            '00:00:20.000', 
            unittest.mock.ANY, 
            is_smart_cut=False,
            tracks=unittest.mock.ANY,
            progress_callback=unittest.mock.ANY
        )
        # Kiểm tra call thứ hai
        self.mock_cut_video.assert_any_call(
            '/fake/video.mp4',
            unittest.mock.ANY,
            '00:00:30.000', 
            '00:00:40.200', 
            unittest.mock.ANY,
            is_smart_cut=False,
            tracks=unittest.mock.ANY,
            progress_callback=unittest.mock.ANY
        )
        self.mock_merge_videos.assert_not_called()


    def test_export_merge_mode_with_cleanup(self):
        """Kiểm tra chế độ export 'Merge' với cleanup."""
        # --- Setup --- #
        self.basic_tab.segments = [
            {'start': 1.0, 'end': 2.0},
            {'start': 3.0, 'end': 4.0}
        ]
        self.basic_tab.segments_widget.cb_export_mode.currentData.return_value = 'merge'
        self.basic_tab.segments_widget.chk_cleanup.isChecked.return_value = True

        # --- Thực thi --- #
        self.basic_tab.export_segments_action()

        # --- Khẳng định --- #
        self.assertEqual(self.mock_cut_video.call_count, 2)
        self.mock_merge_videos.assert_called_once()

        # Kiểm tra các file tạm được tạo ra
        temp_file1 = os.path.join(self.mock_output_dir, 'temp_video_0.mp4')
        temp_file2 = os.path.join(self.mock_output_dir, 'temp_video_1.mp4')
        
        # Kiểm tra merge được gọi với đúng danh sách file tạm
        self.mock_merge_videos.assert_called_with([temp_file1, temp_file2], os.path.join(self.mock_output_dir, 'video_merged.mp4'))
        
        # Kiểm tra các file tạm đã bị xóa
        self.assertEqual(self.mock_os_remove.call_count, 2)
        self.mock_os_remove.assert_any_call(temp_file1)
        self.mock_os_remove.assert_any_call(temp_file2)

    def test_export_merge_mode_no_cleanup(self):
        """Kiểm tra chế độ export 'Merge' không cleanup."""
        # --- Setup --- #
        self.basic_tab.segments = [
            {'start': 5.0, 'end': 8.0}
        ]
        self.basic_tab.segments_widget.cb_export_mode.currentData.return_value = 'merge'
        self.basic_tab.segments_widget.chk_cleanup.isChecked.return_value = False

        # --- Thực thi --- #
        self.basic_tab.export_segments_action()

        # --- Khẳng định --- #
        self.mock_cut_video.assert_called_once()
        self.mock_merge_videos.assert_called_once()
        self.mock_os_remove.assert_not_called() # Không xóa file tạm


    def test_export_stops_if_no_segments(self):
        """Kiểm tra việc export không chạy nếu không có segments."""
        # --- Setup --- #
        self.basic_tab.segments = [] # No segments
        
        # --- Thực thi --- #
        self.basic_tab.export_segments_action()
        
        # --- Khẳng định --- #
        self.mock_cut_video.assert_not_called()
        self.mock_merge_videos.assert_not_called()

        # Kiểm tra xem QMessageBox.warning có được gọi không
        self.mock_msg_box.warning.assert_called_once() 

    # Test cho is_audio_discarded không thể thực hiện chính xác ở unit test này
    # vì logic xử lý is_audio_discarded nằm trong get_ffmpeg_cut_cmd 
    # và cách build command của nó, không trực tiếp trong code Python dễ mock.
    # Ta chỉ có thể đảm bảo cờ `is_audio_discarded` được đọc từ UI, còn việc nó
    # có được ffmpeg sử dụng hay không cần integration test. Trong trường hợp này,
    # code hiện tại không truyền cờ này vào cut_video, nên test sẽ pass
    # mà không cần làm gì thêm.


if __name__ == '__main__':
    unittest.main()
