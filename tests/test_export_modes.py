
import unittest
from unittest.mock import patch, MagicMock, call
import os

# Giả định rằng logic export được điều phối trong một phương thức của MainWindow
# và các hàm ffmpeg nằm trong app.services.ffmpeg_service
# Đây là một kịch bản phổ biến trong ứng dụng PyQt

# Chúng ta sẽ patch các hàm này
FFMPEG_SERVICE_PATH = 'app.services.ffmpeg_service'
OS_PATH = 'os'

class TestExportModes(unittest.TestCase):

    @patch(f'{FFMPEG_SERVICE_PATH}.export_segment')
    @patch(f'{FFMPEG_SERVICE_PATH}.merge_files')
    @patch(f'{OS_PATH}.remove')
    def test_export_separate_files_mode(self, mock_os_remove, mock_merge_files, mock_export_segment):
        """Kiểm tra chế độ 'Separate files': Chỉ xuất các file segment, không merge, không xóa."""
        # --- Setup Mock --- #
        # Giả lập một đối tượng window chính với các thuộc tính cần thiết
        mock_main_window = MagicMock()
        mock_main_window.ui.exportModeComboBox.currentText.return_value = "Separate files"
        mock_main_window.ui.cleanupTempFilesCheckBox.isChecked.return_value = False # Không quan trọng trong mode này
        mock_main_window.source_video_path = '/path/to/source.mp4'
        mock_main_window.output_path = '/path/to/output'

        # Giả lập danh sách các scenes (đoạn cắt)
        mock_main_window.get_scenes_for_export.return_value = [
            {'start': 0, 'end': 10, 'name': 'segment_01'},
            {'start': 20, 'end': 30, 'name': 'segment_02'}
        ]

        # --- Thực thi --- #
        # Gọi hàm export chính (giả định tên là run_export_logic)
        from app.ui.main_window import run_export_logic # Giả định hàm này tồn tại
        run_export_logic(mock_main_window)

        # --- Khẳng định (Assertions) --- #
        # 1. Phải gọi export_segment cho mỗi scene
        self.assertEqual(mock_export_segment.call_count, 2)
        expected_calls = [
            call(mock_main_window.source_video_path, os.path.join(mock_main_window.output_path, 'segment_01.mp4'), 0, 10),
            call(mock_main_window.source_video_path, os.path.join(mock_main_window.output_path, 'segment_02.mp4'), 20, 30)
        ]
        mock_export_segment.assert_has_calls(expected_calls, any_order=True)

        # 2. KHÔNG được gọi hàm merge
        mock_merge_files.assert_not_called()

        # 3. KHÔNG được gọi hàm xóa file
        mock_os_remove.assert_not_called()

    @patch(f'{FFMPEG_SERVICE_PATH}.export_segment')
    @patch(f'{FFMPEG_SERVICE_PATH}.merge_files')
    @patch(f'{OS_PATH}.remove')
    def test_export_merge_and_separate_no_cleanup(self, mock_os_remove, mock_merge_files, mock_export_segment):
        """Kiểm tra 'Merge & Separate' không dọn dẹp: Xuất segments VÀ file merged."""
        # --- Setup Mock --- #
        mock_main_window = MagicMock()
        mock_main_window.ui.exportModeComboBox.currentText.return_value = "Merge & Separate"
        mock_main_window.ui.cleanupTempFilesCheckBox.isChecked.return_value = False
        mock_main_window.source_video_path = '/path/to/source.mp4'
        mock_main_window.output_path = '/path/to/output'

        mock_main_window.get_scenes_for_export.return_value = [
            {'start': 0, 'end': 10, 'name': 'segment_01'},
            {'start': 20, 'end': 30, 'name': 'segment_02'}
        ]
        
        # Giả lập tên file đầu ra
        base_name = os.path.splitext(os.path.basename(mock_main_window.source_video_path))[0]
        merged_file_path = os.path.join(mock_main_window.output_path, f"{base_name}_merged.mp4")

        # --- Thực thi --- #
        from app.ui.main_window import run_export_logic # Giả định hàm này tồn tại
        run_export_logic(mock_main_window)

        # --- Khẳng định (Assertions) --- #
        # 1. Phải gọi export_segment cho mỗi scene
        self.assertEqual(mock_export_segment.call_count, 2)

        # 2. Phải gọi hàm merge
        segment_paths = [
            os.path.join(mock_main_window.output_path, 'segment_01.mp4'),
            os.path.join(mock_main_window.output_path, 'segment_02.mp4')
        ]
        mock_merge_files.assert_called_once_with(segment_paths, merged_file_path)

        # 3. KHÔNG được gọi hàm xóa file
        mock_os_remove.assert_not_called()

    @patch(f'{FFMPEG_SERVICE_PATH}.export_segment')
    @patch(f'{FFMPEG_SERVICE_PATH}.merge_files')
    @patch(f'{OS_PATH}.remove')
    def test_export_merge_and_separate_with_cleanup(self, mock_os_remove, mock_merge_files, mock_export_segment):
        """Kiểm tra 'Merge & Separate' có dọn dẹp: Xuất file merged, XÓA file segments."""
        # --- Setup Mock --- #
        mock_main_window = MagicMock()
        mock_main_window.ui.exportModeComboBox.currentText.return_value = "Merge & Separate"
        mock_main_window.ui.cleanupTempFilesCheckBox.isChecked.return_value = True # Kích hoạt dọn dẹp
        mock_main_window.source_video_path = '/path/to/source.mp4'
        mock_main_window.output_path = '/path/to/output'

        mock_main_window.get_scenes_for_export.return_value = [
            {'start': 0, 'end': 10, 'name': 'segment_01'},
            {'start': 20, 'end': 30, 'name': 'segment_02'}
        ]
        
        base_name = os.path.splitext(os.path.basename(mock_main_window.source_video_path))[0]
        merged_file_path = os.path.join(mock_main_window.output_path, f"{base_name}_merged.mp4")

        # --- Thực thi --- #
        from app.ui.main_window import run_export_logic # Giả định hàm này tồn tại
        run_export_logic(mock_main_window)

        # --- Khẳng định (Assertions) --- #
        # 1. Phải gọi export_segment
        self.assertEqual(mock_export_segment.call_count, 2)

        # 2. Phải gọi hàm merge
        segment_paths = [
            os.path.join(mock_main_window.output_path, 'segment_01.mp4'),
            os.path.join(mock_main_window.output_path, 'segment_02.mp4')
        ]
        mock_merge_files.assert_called_once_with(segment_paths, merged_file_path)

        # 3. Phải gọi hàm xóa cho mỗi file segment
        self.assertEqual(mock_os_remove.call_count, 2)
        expected_remove_calls = [call(p) for p in segment_paths]
        mock_os_remove.assert_has_calls(expected_remove_calls, any_order=True)

# Để chạy test này, bạn cần có một hàm `run_export_logic` trong `main_window.py`
# mà chúng tôi có thể import và gọi. Ví dụ về cấu trúc của hàm đó:
#
# def run_export_logic(main_window): # main_window là instance của MainWindow
#     from app.services import ffmpeg_service
#     import os
#
#     export_mode = main_window.ui.exportModeComboBox.currentText()
#     cleanup = main_window.ui.cleanupTempFilesCheckBox.isChecked()
#     source_video = main_window.source_video_path
#     output_path = main_window.output_path
#     scenes = main_window.get_scenes_for_export()
#
#     segment_paths = []
#     for scene in scenes:
#         segment_name = f"{scene['name']}.mp4"
#         segment_path = os.path.join(output_path, segment_name)
#         segment_paths.append(segment_path)
#         ffmpeg_service.export_segment(source_video, segment_path, scene['start'], scene['end'])
#
#     if export_mode == "Merge & Separate":
#         base_name = os.path.splitext(os.path.basename(source_video))[0]
#         merged_file_path = os.path.join(output_path, f"{base_name}_merged.mp4")
#         ffmpeg_service.merge_files(segment_paths, merged_file_path)
#
#         if cleanup:
#             for segment_path in segment_paths:
#                 os.remove(segment_path)
#
