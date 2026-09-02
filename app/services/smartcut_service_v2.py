import os
import shutil
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

from app.core.helpers import get_origin_tbn_fps
import app.services.ffmpeg_service as ffmpeg_service
from app.core.keyframes_helper import (
    get_video_keyframes,
    plan_smart_cut_segment,
    cut_copy_subpart,
    encode_subpart
)

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

    def run(self):
        try:
            export_mode = self.options.get("export_mode", "separate")
            is_smart_cut = self.options.get("is_smart_cut", True)
            do_cleanup = self.options.get("do_cleanup", True)
            base_name, ext = os.path.splitext(os.path.basename(self.input_path))

            self.log_signal.emit("[SmartCut] Analyzing keyframes...")
            keyframes = get_video_keyframes(self.input_path)
            self.log_signal.emit(f"[SmartCut] Found {len(keyframes)} keyframes.")

            fps_tbn = get_origin_tbn_fps(self.input_path)
            timescale = fps_tbn[1] if len(fps_tbn) > 1 else None

            processed_segment_files = []

            for seg_idx, segment in enumerate(self.segments):
                start_sec = float(segment["start"])
                end_sec = float(segment["end"])
                self.log_signal.emit(f"\n[Segment {seg_idx+1}] Range: {start_sec:.3f}s -> {end_sec:.3f}s")

                # plan = plan_smart_cut_segment(start_sec, end_sec, keyframes, self.input_path) if is_smart_cut else [{"type": "copy", "start": start_sec, "end": end_sec}]
                plan = plan_smart_cut_segment(start_sec, end_sec, keyframes, input_path=self.input_path) if is_smart_cut else [{"type": "copy", "start": start_sec, "end": end_sec}]

                part_files = []
                for part_idx, part in enumerate(plan):
                    p_start, p_end, p_type = part["start"], part["end"], part["type"]
                    p_dur = p_end - p_start

                    if p_dur <= 0.001:
                        continue

                    part_file = os.path.join(self.dest_dir, f"tmp_seg_{seg_idx+1}_part_{part_idx+1}_{p_type}{ext}")
                    part_files.append(part_file)

                    if p_type == "copy":
                        self.log_signal.emit(f"  -> Part {part_idx+1}: LOSSLESS COPY ({p_start:.3f}s -> {p_end:.3f}s)")
                        cut_copy_subpart(self.input_path, p_start, p_dur, part_file, timescale)
                    else:
                        self.log_signal.emit(f"  -> Part {part_idx+1}: RE-ENCODE ({p_start:.3f}s -> {p_end:.3f}s)")
                        encode_subpart(self.input_path, p_start, p_dur, part_file)

                # Ghép các part thành 1 segment hoàn chỉnh
                if len(part_files) == 1:
                    seg_final_file = part_files[0]
                else:
                    seg_final_file = os.path.join(self.dest_dir, f"tmp_seg_{seg_idx+1}_complete{ext}")
                    ffmpeg_service.merge_videos_v2(part_files, seg_final_file)
                    
                    for pf in part_files:
                        if os.path.exists(pf) and pf != seg_final_file:
                            try: os.remove(pf)
                            except Exception: pass

                processed_segment_files.append(seg_final_file)

            # Xuất file đầu ra
            if export_mode == "separate":
                for i, seg_file in enumerate(processed_segment_files):
                    start_str = ffmpeg_service.format_seconds_to_time(self.segments[i]["start"]).replace(":", "-")
                    end_str = ffmpeg_service.format_seconds_to_time(self.segments[i]["end"]).replace(":", "-")
                    out_name = os.path.join(self.dest_dir, f"{base_name}_seg{i+1}_{start_str}_{end_str}{ext}")
                    if os.path.exists(out_name):
                        os.remove(out_name)
                    shutil.move(seg_file, out_name)

                self.finished_signal.emit(f"Exported {len(self.segments)} SmartCut segments!")

            elif export_mode == "merge":
                final_output = os.path.join(self.dest_dir, f"{base_name}_smartcut_merged{ext}")
                self.log_signal.emit(f"\n[Merge] Final Output: {final_output}")
                ffmpeg_service.merge_videos_v2(processed_segment_files, final_output)

                if do_cleanup:
                    for sf in processed_segment_files:
                        if os.path.exists(sf):
                            try: os.remove(sf)
                            except Exception: pass

                self.finished_signal.emit(f"Merged video: {os.path.basename(final_output)}")

        except Exception as e:
            self.log_signal.emit(f"\n[ERROR]\n{traceback.format_exc()}")
            self.error_signal.emit(f"SmartCut Failed: {str(e)}")