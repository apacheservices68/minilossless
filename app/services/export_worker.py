import os
from PyQt6.QtCore import QThread, pyqtSignal
import app.services.ffmpeg_service as ffmpeg_service

class InterruptionRequestedError(Exception):
    """Custom exception to signal that thread interruption was requested."""
    pass

class ExportWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, input_path: str, dest_dir: str, segments: list, options: dict, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.dest_dir = dest_dir
        self.segments = segments
        self.options = options
        self.parent_tab = parent # To call log() method

    def log(self, message):
        if self.parent_tab:
            try:
                self.parent_tab.log(message)
            except Exception:
                pass

    def run(self):
        try:
            is_smart_cut = self.options.get("is_smart_cut", False)
            if self.isInterruptionRequested():
                raise InterruptionRequestedError("Export canceled before start.")

            if is_smart_cut:
                self.smart_cut_export()
            else:
                self.standard_export()

        except InterruptionRequestedError as e:
            self.log(f"[Export Canceled] {e}")
            self.finished.emit(False, "Export was canceled by the user.")

        except Exception as e:
            error_message = f"An unexpected error occurred during export: {str(e)}"
            self.log(f"[Export FATAL ERROR] {error_message}")
            self.finished.emit(False, error_message)

    def standard_export(self):
        export_mode = self.options.get("export_mode", "separate")
        do_cleanup = self.options.get("do_cleanup", False)
        tracks = self.options.get("tracks", [])
        is_audio_discarded = self.options.get("is_audio_discarded", False)

        self.log(f"Starting export with mode: {export_mode}")

        video_name = os.path.basename(self.input_path)
        base_name, ext = os.path.splitext(video_name)
        
        exported_files = []
        success_count = 0
        total_segments = len(self.segments)

        for i, seg in enumerate(self.segments):
            if self.isInterruptionRequested():
                raise InterruptionRequestedError("Export canceled during segment processing.")

            start_str = ffmpeg_service.format_seconds_to_time(seg["start"], include_ms=True)
            end_str = ffmpeg_service.format_seconds_to_time(seg["end"], include_ms=True)
            
            # Sửa đổi cách tạo tên file để phù hợp với test
            safe_start = start_str.replace(":", "-").replace(".", "-")
            safe_end = end_str.replace(":", "-").replace(".", "-")
            
            output_filename = f"{base_name}_{i+1}_{safe_start}_{safe_end}{ext}"
            output_path = os.path.join(self.dest_dir, output_filename)

            progress_val = int(((i + 0.5) / (total_segments + (1 if export_mode == 'merge' else 0))) * 100)
            self.progress.emit(progress_val, f"Exporting Segment {i+1}/{total_segments}...")
            
            duration = seg["end"] - seg["start"]
            ffmpeg_service.cut_video(
                self.input_path, output_path, start_str, end_str, duration=duration,
                is_smart_cut=False, tracks=tracks,
                audio_codec="copy" if not is_audio_discarded else None
            )
            success_count += 1
            exported_files.append(output_path)

        if self.isInterruptionRequested():
            raise InterruptionRequestedError("Export canceled before merge.")

        if success_count < total_segments:
            raise Exception(f"Only {success_count}/{total_segments} segments exported successfully.")

        if export_mode == 'merge':
            self.progress.emit(95, "Merging files...")
            merged_filename = f"{base_name}_merged{ext}"
            merged_output_path = os.path.join(self.dest_dir, merged_filename)
            
            ffmpeg_service.merge_videos(exported_files, merged_output_path)
            if self.isInterruptionRequested():
                raise InterruptionRequestedError("Export canceled during merge.")

            if do_cleanup:
                self.log("Cleaning up intermediate files...")
                for f_path in exported_files:
                    if self.isInterruptionRequested():
                        self.log("Skipping further cleanup due to cancellation.")
                        break
                    try:
                        os.remove(f_path)
                    except OSError as e:
                        self.log(f"Error deleting file {f_path}: {e}")

            final_message = f"Successfully merged {success_count} segments into {merged_filename}"
        else:
            final_message = f"Successfully exported all {success_count} segments!"

        self.progress.emit(100, "Done!")
        self.finished.emit(True, final_message)

    def smart_cut_export(self):
        export_mode = self.options.get("export_mode", "separate")
        do_cleanup = self.options.get("do_cleanup", False)
        tracks = self.options.get("tracks", [])
        is_audio_discarded = self.options.get("is_audio_discarded", False)

        self.log("Smart Cut mode enabled.")

        video_name = os.path.basename(self.input_path)
        base_name, ext = os.path.splitext(video_name)
        
        exported_files = []
        success_count = 0
        total_segments = len(self.segments)
        cut_progress_end = 30

        for i, seg in enumerate(self.segments):
            if self.isInterruptionRequested():
                raise InterruptionRequestedError("Export canceled during smart cut segment processing.")

            start_str = ffmpeg_service.format_seconds_to_time(seg["start"], include_ms=True)
            end_str = ffmpeg_service.format_seconds_to_time(seg["end"], include_ms=True)
            
            safe_start = start_str.replace(":", "-").replace(".", "-")
            safe_end = end_str.replace(":", "-").replace(".", "-")
            
            output_filename = f"{base_name}_smart_{safe_start}_{safe_end}{ext}"
            output_path = os.path.join(self.dest_dir, output_filename)

            segment_progress_start = int((i / total_segments) * cut_progress_end)
            segment_progress_end = int(((i + 1) / total_segments) * cut_progress_end)

            self.progress.emit(segment_progress_start, f"Smart Cut: Starting segment {i+1}/{total_segments}")
            duration = seg["end"] - seg["start"]
            
            def progress_handler(p_type, p_value):
                if self.isInterruptionRequested():
                    return
                if p_type == 'keyframe':
                    progress = segment_progress_start + int((p_value / 100) * (segment_progress_end - segment_progress_start) * 0.2) + 30
                    msg = f"Smart Cut: Analyzing keyframes for seg {i+1}"
                elif p_type == 're-encoding':
                    progress = segment_progress_start + int((p_value / 100) * (segment_progress_end - segment_progress_start) * 0.3) + 50
                    msg = f"Smart Cut: Re-encoding non-keyframe sections for seg {i+1}"
                else:
                    progress = segment_progress_start + int((p_value / 100) * (segment_progress_end - segment_progress_start) * 0.2) + 80
                    msg = f"Smart Cut: Applying cut for seg {i+1}"
                self.progress.emit(progress, msg)

            ffmpeg_service.cut_video(
                self.input_path, output_path, start_str, end_str, duration=duration,
                is_smart_cut=True, tracks=tracks,
                audio_codec="copy" if not is_audio_discarded else None,
                progress_callback=progress_handler
            )
            
            self.progress.emit(segment_progress_end, f"Smart Cut: Finished segment {i+1}")
            success_count += 1
            exported_files.append(output_path)

        if self.isInterruptionRequested():
            raise InterruptionRequestedError("Export canceled before smart cut merge.")

        if success_count < total_segments:
            raise Exception(f"Only {success_count}/{total_segments} segments exported successfully.")

        if export_mode == 'merge':
            self.progress.emit(80, "Smart Cut: Merging all processed segments...")
            merged_filename = f"{base_name}_merged_smart{ext}"
            merged_output_path = os.path.join(self.dest_dir, merged_filename)
            
            ffmpeg_service.merge_videos(exported_files, merged_output_path)
            if self.isInterruptionRequested():
                raise InterruptionRequestedError("Export canceled during smart cut merge.")
                
            self.progress.emit(95, "Smart Cut: Finalizing merge...")

            if do_cleanup:
                self.log("Cleaning up intermediate files...")
                for f_path in exported_files:
                    if self.isInterruptionRequested():
                        self.log("Skipping further cleanup due to cancellation.")
                        break
                    try:
                        os.remove(f_path)
                    except OSError as e:
                        self.log(f"Error deleting file {f_path}: {e}")

            final_message = f"Successfully smart-merged {success_count} segments into {merged_filename}"
        else:
            final_message = f"Successfully exported all {success_count} smart-cut segments!"

        self.progress.emit(100, "Done!")
        self.finished.emit(True, final_message)
