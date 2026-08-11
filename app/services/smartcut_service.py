import os
from PyQt6.QtCore import QThread, pyqtSignal
import app.services.ffmpeg_service as ffmpeg_service

class SmartCutWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, input_path: str, dest_dir: str, segments: list, options: dict, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.dest_dir = dest_dir
        self.segments = segments
        self.options = options

    def run(self):
        try:
            export_mode = self.options.get("export_mode", "separate")
            is_smart_cut = self.options.get("is_smart_cut", True)
            tracks = self.options.get("tracks")
            do_cleanup = self.options.get("do_cleanup", False)

            self.log_signal.emit(f"Starting Smartcut in '{export_mode}' mode...")

            if export_mode == "separate":
                for i, segment in enumerate(self.segments):
                    start_time = ffmpeg_service.format_seconds_to_time(segment["start"])
                    end_time = ffmpeg_service.format_seconds_to_time(segment["end"])
                    duration = segment["end"] - segment["start"]
                    base_name, ext = os.path.splitext(os.path.basename(self.input_path))
                    output_filename = f"{base_name}_{i+1}_{start_time.replace(':', '-')}_{end_time.replace(':', '-')}{ext}"
                    output_path = os.path.join(self.dest_dir, output_filename)

                    self.log_signal.emit(f"Exporting segment {i+1}/{len(self.segments)} to {output_path}...")
                    
                    ffmpeg_service.cut_video(
                        self.input_path, 
                        output_path, 
                        start_time, 
                        end_time, 
                        duration,
                        is_smart_cut=is_smart_cut,
                        tracks=tracks,
                        progress_callback=lambda status, progress, idx=i: self.log_signal.emit(f"[Cut Segment {idx+1}] {status} at {progress}%")
                    )

                final_message = f"Successfully exported {len(self.segments)} separate files."
                self.log_signal.emit(final_message)
                self.finished_signal.emit(final_message)

            elif export_mode == "merge":
                temp_files = []
                base_name, ext = os.path.splitext(os.path.basename(self.input_path))

                for i, segment in enumerate(self.segments):
                    start_time = ffmpeg_service.format_seconds_to_time(segment["start"])
                    end_time = ffmpeg_service.format_seconds_to_time(segment["end"])
                    duration = segment["end"] - segment["start"]
                    temp_filename = os.path.join(self.dest_dir, f"temp_{base_name}_{i}{ext}")
                    temp_files.append(temp_filename)

                    self.log_signal.emit(f"Cutting segment {i+1}/{len(self.segments)} for merge...")
                    
                    ffmpeg_service.cut_video(
                        self.input_path, 
                        temp_filename, 
                        start_time, 
                        end_time, 
                        duration,
                        is_smart_cut=is_smart_cut,
                        tracks=tracks,
                        progress_callback=lambda status, progress, idx=i: self.log_signal.emit(f"[Cut Segment {idx+1}] {status} at {progress}%")
                    )

                output_filename = f"{base_name}_merged{ext}"
                output_path = os.path.join(self.dest_dir, output_filename)
                self.log_signal.emit(f"Merging {len(temp_files)} segments into {output_path}...")
                ffmpeg_service.merge_videos(temp_files, output_path)

                if do_cleanup:
                    self.log_signal.emit("Cleaning up temporary files...")
                    for f in temp_files:
                        try:
                            if os.path.exists(f):
                                os.remove(f)
                        except OSError as e:
                            self.log_signal.emit(f"Could not remove temp file {f}: {e}")

                final_message = f"Successfully merged segments into {output_filename}."
                self.log_signal.emit(final_message)
                self.finished_signal.emit(final_message)

        except Exception as e:
            error_message = f"An error occurred during Smartcut: {str(e)}"
            self.log_signal.emit(error_message)
            self.error_signal.emit(error_message)
