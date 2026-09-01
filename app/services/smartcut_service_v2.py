import os
import tempfile
import subprocess
import shutil
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

from app.core.helpers import get_video_codec
import app.services.ffmpeg_service as ffmpeg_service
from app.core.keyframes_helper import encode_subpart, get_video_keyframes, plan_smart_cut_segment
from app.core.ffmpeg_resolver import get_ffmpeg_path
# from app.core.helpers import get_origin_bitrate


class SmartCutWorkerV2(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, input_path: str, dest_dir: str, segments: list, options: dict, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.dest_dir = dest_dir
        self.segments = segments
        self.options = options
        self.parent = parent
        self.ffmpeg_path = get_ffmpeg_path()

    def run(self):
        try:
            export_mode = self.options.get("export_mode", "separate")
            is_smart_cut = self.options.get("is_smart_cut", True)
            do_cleanup = self.options.get("do_cleanup", True)
            base_name, ext = os.path.splitext(os.path.basename(self.input_path))

            self.log_signal.emit("[SmartCut v2] Analyzing video keyframes with ffprobe...")
            keyframes = get_video_keyframes(self.input_path)
            self.log_signal.emit(f"[SmartCut v2] Found {len(keyframes)} keyframes.")

            processed_segment_files = []

            is_mov_file = self.input_path.lower().endswith('.mov')
            codec = get_video_codec(self.input_path)
            
            is_hevc = True if codec == "hevc" else False
            print(f"Input video codec: {codec} | is_hevc={is_hevc}")
            for seg_idx, segment in enumerate(self.segments):
                start_sec = segment["start"]
                end_sec = segment["end"]
                self.log_signal.emit(f"\n[Segment {seg_idx+1}] Processing: {start_sec:.3f}s -> {end_sec:.3f}s")

                if is_smart_cut:
                    plan = plan_smart_cut_segment(start_sec, end_sec, keyframes)
                else:
                    # Nếu tắt smartcut -> Fast cut trực tiếp (Lossless copy)
                    plan = [{"type": "copy", "start": start_sec, "end": end_sec}]

                part_files = []
                for part_idx, part in enumerate(plan):
                    p_start = part["start"]
                    p_end = part["end"]
                    p_type = part["type"]
                    p_dur = p_end - p_start

                    if p_dur <= 0.001:
                        continue

                    part_file = os.path.join(
                        self.dest_dir, f"tmp_seg_{seg_idx+1}_part_{part_idx+1}_{p_type}{ext}"
                    )
                    part_files.append(part_file)

                    if p_type == "copy" and not is_mov_file and is_hevc == False:
                        self.log_signal.emit(f"  -> Part {part_idx+1}: LOSSLESS COPY ({p_start:.3f}s -> {p_end:.3f}s)")
                        ffmpeg_service.cut_video(
                            self.input_path, part_file,
                            ffmpeg_service.format_seconds_to_time(p_start),
                            ffmpeg_service.format_seconds_to_time(p_end),
                            p_dur, is_smart_cut=False
                        )
                    else:
                        # self.log_signal.emit(f"  -> Part {part_idx+1}: SMART RE-ENCODE ({p_start:.3f}s -> {p_end:.3f}s)")
                        # encode_subpart(self.input_path, p_start, p_dur, part_file)
                        # File MOV (hoặc các part dạng 'encode') -> Re-encode bằng encode_subpart
                        action_name = "SMART RE-ENCODE (MOV Force)" if is_mov_file else "SMART RE-ENCODE"
                        self.log_signal.emit(f"  -> Part {part_idx+1}: {action_name} ({p_start:.3f}s -> {p_end:.3f}s)")
                        encode_subpart(self.input_path, p_start, p_dur, part_file)

                # Ghép các part nhỏ thành 1 segment hoàn chỉnh
                if len(part_files) == 1:
                    seg_final_file = part_files[0]
                else:
                    seg_final_file = os.path.join(self.dest_dir, f"tmp_seg_{seg_idx+1}_complete{ext}")
                    ffmpeg_service.merge_videos_v2(part_files, seg_final_file)
                    #Cleanup subparts
                    for pf in part_files:
                        if os.path.exists(pf) and pf != seg_final_file:
                            try:
                                os.remove(pf)
                            except Exception:
                                pass

                processed_segment_files.append(seg_final_file)

            # Xử lý theo Export Mode người dùng đã chọn
            if export_mode == "separate":
                for i, seg_file in enumerate(processed_segment_files):
                    start_str = ffmpeg_service.format_seconds_to_time(self.segments[i]["start"]).replace(":", "-")
                    end_str = ffmpeg_service.format_seconds_to_time(self.segments[i]["end"]).replace(":", "-")
                    out_name = os.path.join(self.dest_dir, f"{base_name}_seg{i+1}_{start_str}_{end_str}{ext}")
                    if os.path.exists(out_name):
                        os.remove(out_name)
                    shutil.move(seg_file, out_name)

                msg = f"Successfully exported {len(self.segments)} SmartCut segments!"
                self.log_signal.emit(msg)
                self.finished_signal.emit(msg)

            elif export_mode == "merge":
                final_output = os.path.join(self.dest_dir, f"{base_name}_smartcut_merged{ext}")
                self.log_signal.emit(f"\n[Merge] Merging all segments into: {final_output}")
                ffmpeg_service.merge_videos(processed_segment_files, final_output)

                if do_cleanup:
                    for sf in processed_segment_files:
                        if os.path.exists(sf):
                            os.remove(sf)

                msg = f"Successfully merged SmartCut video: {os.path.basename(final_output)}"
                self.log_signal.emit(msg)
                self.finished_signal.emit(msg)

        except Exception as e:
            # Lấy toàn bộ chi tiết traceback (file name, line number, code call stack)
            tb_str = traceback.format_exc()
            
            # Lấy thông tin dòng bị lỗi trực tiếp cuối cùng
            tb = traceback.extract_tb(e.__traceback__)
            if tb:
                last_call = tb[-1]
                file_name = os.path.basename(last_call.filename)
                line_no = last_call.lineno
                func_name = last_call.name
                err_msg = f"SmartCut v2 Failed in [{file_name}:{line_no}] ({func_name}): {str(e)}"
            else:
                err_msg = f"SmartCut v2 Failed: {str(e)}"

            # Gửi cả thông tin chi tiết và StackTrace đầy đủ ra Console
            self.log_signal.emit(f"\n[ERROR DETAILS]\n{tb_str}")
            self.error_signal.emit(err_msg)