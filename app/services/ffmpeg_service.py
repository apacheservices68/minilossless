import subprocess
import os
import tempfile
import cv2
import numpy as np
import json
import ffmpeg
from app.services.exact_cut_service import exact_cut as exact_cut_video
from app.core.ffmpeg_config import (
    get_ffmpeg_cut_cmd,
    get_ffmpeg_merge_cmd,
    get_ffmpeg_watermark_cmd,
    get_ffmpeg_pipe_cmd,
    get_ffmpeg_exact_cut_cmd,
    get_ffmpeg_snapshot_cmd,
    get_ffmpeg_export_cmd
)
from app.core.ffmpeg_resolver import get_ffprobe_path, get_ffmpeg_path

def get_video_info(input_path: str) -> dict:
    """Run ffprobe to get video info."""
    ffprobe_path = get_ffprobe_path()
    if not ffprobe_path:
        raise FileNotFoundError("ffprobe executable not found.")
    cmd = [
        ffprobe_path, "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", input_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error getting video info: {e}")
        return {}

def parse_time_to_seconds(t_str: str) -> float:
    """
    Parse HH:MM:SS or HH:MM:SS.mmm or MM:SS or SS format to seconds (float).
    """
    t_str = t_str.strip()
    if not t_str:
        return 0.0
    try:
        if ":" in t_str:
            parts = t_str.split(":")
            if len(parts) == 3:
                h, m, s = parts
                return float(h) * 3600 + float(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                return float(m) * 60 + float(s)
        return float(t_str)
    except ValueError:
        return 0.0

def format_seconds_to_time(sec: float, include_ms: bool = True) -> str:
    """
    Format float seconds to HH:MM:SS.mmm or HH:MM:SS.
    """
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:
        s += 1
        ms -= 1000
    if s >= 60:
        m += 1
        s -= 60
    if m >= 60:
        h += 1
        m -= 60
        
    if include_ms:
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    else:
        return f"{h:02d}:{m:02d}:{s:02d}"

def cut_video(input_path: str, output_path: str, start_time: str, end_time: str, duration: float, is_smart_cut: bool = False, tracks: list = None, audio_codec: str = "copy") -> bool:
    if is_smart_cut:
        return exact_cut_video(input_path, output_path, start_time, duration, tracks)

    # Original lossless cut logic
    try:
        cmd = get_ffmpeg_cut_cmd(input_path, output_path, start_time, end_time, tracks, audio_codec)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, universal_newlines=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in lossless_cut: {e.stderr}")
        raise Exception(e.stderr)

def merge_videos(video_paths: list[str], output_path: str) -> bool:
    """
    Merge multiple videos of the same format without re-encoding using concat demuxer.
    """
    if not video_paths:
        raise ValueError("No video files provided for merging.")
    
    temp_list = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            temp_list = f.name
            for path in video_paths:
                escaped_path = path.replace("\"", "\"\\\"\"")
                f.write(f"file ‘{escaped_path}’\n")
        
        cmd = get_ffmpeg_merge_cmd(temp_list, output_path)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in merge_videos: {e.stderr}")
        raise Exception(e.stderr)
    finally:
        if temp_list and os.path.exists(temp_list):
            os.remove(temp_list)

def create_text_watermark_image(text: str, output_image_path: str) -> None:
    """
    Render text to a transparent PNG file using Pillow with white text and black outline.
    """
    from PIL import Image, ImageDraw, ImageFont
    
    font_names = ["DejaVuSans.ttf", "arial.ttf", "LiberationSans-Regular.ttf", "FreeSans.ttf"]
    font = None
    for name in font_names:
        try:
            font = ImageFont.truetype(name, 24)
            break
        except IOError:
            continue
            
    if font is None:
        try:
            font = ImageFont.load_default(size=24)
        except TypeError:
            font = ImageFont.load_default()

    dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_img)
    
    try:
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        padding = 10
        img_width = int(text_width + 2 * padding)
        img_height = int(text_height + 2 * padding)
        offset_x = padding - bbox[0]
        offset_y = padding - bbox[1]
    except AttributeError:
        text_width, text_height = dummy_draw.textsize(text, font=font)
        padding = 10
        img_width = int(text_width + 2 * padding)
        img_height = int(text_height + 2 * padding)
        offset_x = padding
        offset_y = padding

    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        draw.text((offset_x, offset_y), text, font=font, fill=(255, 255, 255, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0, 255))
    except TypeError:
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2),
                       (-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
            draw.text((offset_x + dx, offset_y + dy), text, font=font, fill=(0, 0, 0, 255))
        draw.text((offset_x, offset_y), text, font=font, fill=(255, 255, 255, 255))

    img.save(output_image_path, "PNG")

def watermark_video(input_path: str, output_path: str, text: str, position: str) -> bool:
    """
    Add a text watermark to video using Pillow-generated image and FFmpeg overlay.
    """
    temp_watermark = "temp_watermark.png"
    
    try:
        create_text_watermark_image(text, temp_watermark)
        
        pos_map = {
            "top_left": "x=10:y=10",
            "top_right": "x=W-w-10:y=10",
            "bottom_left": "x=10:y=H-h-10",
            "bottom_right": "x=W-w-10:y=H-h-10"
        }
        
        coords = pos_map.get(position, "x=10:y=10")
        
        cmd = get_ffmpeg_watermark_cmd(input_path, output_path, temp_watermark, coords)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in watermark_video: {e.stderr}")
        raise Exception(e.stderr)
    finally:
        if os.path.exists(temp_watermark):
            try:
                os.remove(temp_watermark)
            except Exception as e:
                print(f"Failed to remove temporary watermark file: {e}")

def process_video_ai(
    input_video_path: str = None,
    output_video_path: str = None,
    texts: list = None,
    use_cuda: bool = False,
    face_blur_enabled: bool = False,
    face_blur_pct: float = 0.0,
    face_blur_type: str = "Square",
    face_blur_image_path: str = None,
    face_blur_style: str = "Gaussian",
    face_blur_strength: int = 15,
    bg_blur_enabled: bool = False,
    bg_blur_strength: int = 101,
    signals = None,
    preview_width=0, 
    preview_height=0,
    progress_callback = None,
    *args,    
    **kwargs
):
    """
    Run the AI process pipeline using Subprocess Popen to push processed frames into FFmpeg.
    """
    input_video_path = input_video_path or kwargs.get("input_path")
    output_video_path = output_video_path or kwargs.get("output_path")
    texts = texts if texts is not None else []
    
    def emit_progress(pct, msg):
        if signals:
            try:
                signals.progress.emit(pct, msg)
            except Exception:
                pass
        if progress_callback:
            try:
                progress_callback(pct, msg)
            except TypeError:
                try:
                    progress_callback(pct)
                except Exception:
                    pass

    from app.core.constants import BASE_DIR
    temp_watermark_path = os.path.join(BASE_DIR, "temp_wm.png")
    
    detector = None
    segmenter = None
    
    if face_blur_enabled:
        from app.ai.detectors import get_face_detector
        detector = get_face_detector()
            
    if bg_blur_enabled:
        from app.ai.detectors import get_selfie_segmenter
        segmenter = get_selfie_segmenter()

    from app.ai.pipeline import AIPipeline
    pipeline = AIPipeline(detector=detector, segmenter=segmenter)

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise Exception(f"Cannot open input video: {input_video_path}")
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    width = width if width % 2 == 0 else width - 1
    height = height if height % 2 == 0 else height - 1

    if fps <= 0 or np.isnan(fps):
        fps = 30.0
    if total_frames <= 0:
        total_frames = 1
        
    process = None
    try:
        if texts:
            from app.services.ai_processor import create_advanced_watermark_image
            create_advanced_watermark_image(
                width, height, texts, temp_watermark_path, 
                preview_width=preview_width, 
                preview_height=preview_height
            )
        
        ffmpeg_cmd = get_ffmpeg_pipe_cmd(
            width=width,
            height=height,
            fps=fps,
            temp_watermark_path=temp_watermark_path,
            input_video_path=input_video_path,
            use_cuda=use_cuda,
            output_video_path=output_video_path
        )
        
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))

            processed_frame = pipeline.process_frame(
                frame=frame,
                face_blur_enabled=face_blur_enabled,
                face_blur_pct=face_blur_pct,
                face_blur_type=face_blur_type,
                face_blur_image_path=face_blur_image_path,
                face_blur_style=face_blur_style,
                face_blur_strength=face_blur_strength,
                bg_blur_enabled=bg_blur_enabled,
                bg_blur_strength=bg_blur_strength
            )
            
            try:
                process.stdin.write(processed_frame.tobytes())
            except Exception:
                break
                
            frame_idx += 1
            pct = int((frame_idx / total_frames) * 100)
            emit_progress(pct, f"Rendering CUDA Frame {frame_idx}/{total_frames} ({pct}%)")
                
    except Exception as e:
        err_msg = str(e)
        if "flush of closed file" not in err_msg and signals:
            try:
                signals.finished.emit(False, err_msg)
            except Exception:
                pass
    finally:
        cap.release()
        
        if process:
            if process.stdin:
                try:
                    process.stdin.close()
                except Exception:
                    pass
                process.stdin = None
            
            try:
                stdout_d, stderr_d = process.communicate()
            except Exception:
                pass
                
        emit_progress(100, "Done!")

        if signals:
            try:
                signals.finished.emit(True, "Processing completed successfully!")
            except Exception:
                pass

        if os.path.exists(temp_watermark_path):
            try:
                os.remove(temp_watermark_path)
            except Exception:
                pass

def get_video_fps(input_path: str) -> float:
    """
    Get the FPS of a video file.
    """
    try:
        ffprobe_path = get_ffprobe_path()
        if not ffprobe_path:
            print("Error getting video FPS: ffprobe not found.")
            return 0.0
        probe = ffmpeg.probe(input_path, cmd=ffprobe_path)
        video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
        if video_stream and "avg_frame_rate" in video_stream:
            num, den = map(int, video_stream["avg_frame_rate"].split("/"))
            if den > 0:
                return num / den
    except Exception as e:
        print(f"Error getting video FPS with ffprobe: {e}")
    return 0.0

def take_snapshot(input_path: str, output_path: str, time: str, quality: int, format: str) -> bool:
    """
    Take a snapshot of a video at a specific time.
    """
    try:
        # FFmpeg quality for JPG is inverted (2-31, lower is better)
        # We map 1-100 (UI) to 31-2 (ffmpeg)
        if format.lower() == 'jpg':
            q_value = int(31 - (quality / 100.0) * 29)
        else:
            q_value = 0 # Not used for PNG

        cmd = get_ffmpeg_snapshot_cmd(input_path, output_path, time, q_value, format)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error taking snapshot: {e.stderr}")
        raise Exception(e.stderr)

def export_video(input_path: str, output_path: str, options: dict) -> bool:
    """Export video with various options (FPS, tracks, metadata)."""
    try:
        cmd = get_ffmpeg_export_cmd(input_path, output_path, options)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in export_video: {e.stderr}")
        raise Exception(e.stderr)
