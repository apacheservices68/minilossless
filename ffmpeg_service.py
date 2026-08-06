import subprocess
import os
import tempfile

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

def cut_video(input_path: str, output_path: str, start_time: str, end_time: str) -> bool:
    """
    Cut video from start_time to end_time without re-encoding.
    start_time, end_time can be in HH:MM:SS or SS format.
    """
    try:
        # Using -ss before -i for fast seeking, and -to for accurate duration
        # With -c copy, this does not re-encode
        cmd = [
            "ffmpeg",
            "-ss", start_time,
            "-to", end_time,
            "-i", input_path,
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in cut_video: {e.stderr}")
        raise Exception(e.stderr)

def merge_videos(video_paths: list[str], output_path: str) -> bool:
    """
    Merge multiple videos of the same format without re-encoding using concat demuxer.
    """
    if not video_paths:
        raise ValueError("No video files provided for merging.")
    
    # Create a temporary file to list all inputs
    temp_list = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            temp_list = f.name
            for path in video_paths:
                # ffmpeg concat demuxer paths need to escape single quotes
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
        
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_list,
            "-c", "copy",
            "-y",
            output_path
        ]
        
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
    
    # Attempt to load a common scalable TrueType font, otherwise fallback to default
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

    # Create a small dummy image to measure text size
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
        # Fallback for older Pillow versions
        text_width, text_height = dummy_draw.textsize(text, font=font)
        padding = 10
        img_width = int(text_width + 2 * padding)
        img_height = int(text_height + 2 * padding)
        offset_x = padding
        offset_y = padding

    # Create the actual watermark image
    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw text with white fill and a robust black outline (stroke)
    try:
        draw.text((offset_x, offset_y), text, font=font, fill=(255, 255, 255, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0, 255))
    except TypeError:
        # Fallback manually drawing stroke if Pillow doesn't support stroke_width
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
        # Create the watermark PNG image
        create_text_watermark_image(text, temp_watermark)
        
        # Map friendly positions to FFmpeg overlay coordinates
        pos_map = {
            "top_left": "x=10:y=10",
            "top_right": "x=W-w-10:y=10",
            "bottom_left": "x=10:y=H-h-10",
            "bottom_right": "x=W-w-10:y=H-h-10"
        }
        
        coords = pos_map.get(position, "x=10:y=10")
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-i", temp_watermark,
            "-filter_complex", f"[0:v][1:v]overlay={coords}[outv]",
            "-map", "[outv]",
            "-map", "0:a?",  # copy audio if present
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in watermark_video: {e.stderr}")
        raise Exception(e.stderr)
    finally:
        # Always clean up the temporary watermark image
        if os.path.exists(temp_watermark):
            try:
                os.remove(temp_watermark)
            except Exception as e:
                print(f"Failed to remove temporary watermark file: {e}")
