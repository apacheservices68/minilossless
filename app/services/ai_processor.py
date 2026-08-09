import math
import os
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtCore import QObject, pyqtSignal
from app.core.constants import BASE_DIR, DEFAULT_FONT_PATH

class AIProcessorSignals(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

def create_advanced_watermark_image(width: int, height: int, texts: list, output_path: str, *args, **kwargs):
    """
    Render multiple advanced draggable texts to a transparent PNG file.
    """
    master_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    for item in texts:
        text_str = item["text"]
        diag = math.hypot(width, height)

        if "rel_center_x" in item:
            center_x = float(item["rel_center_x"]) * width
            center_y = float(item["rel_center_y"]) * height
        else:
            center_x = float(item.get("rel_x", 0)) * width
            center_y = float(item.get("rel_y", 0)) * height

        # Font size calculation
        base_font_size = float(item["rel_font_size"]) * diag
        font_size = max(10, int(round(base_font_size * 1.3333)))

        # Stroke width
        if "stroke_width" in item and item["stroke_width"] is not None:
            stroke_w = int(item["stroke_width"])
        else:
            stroke_w = max(1, int(font_size // 25))
        
        angle = float(item.get("rotation_angle", 0))

        # Opacity calculation
        raw_opacity = item.get("opacity", 1.0)
        try:
            opacity_val = float(raw_opacity)
            if opacity_val > 1.0:
                opacity_val = opacity_val / 100.0
        except (ValueError, TypeError):
            opacity_val = 1.0

        opacity_val = max(0.0, min(1.0, opacity_val))
        alpha = int(round(opacity_val * 255))

        # Font loading
        if os.path.exists(DEFAULT_FONT_PATH):
            font = ImageFont.truetype(DEFAULT_FONT_PATH, font_size)
        else:
            font = ImageFont.load_default()

        dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        dummy_draw = ImageDraw.Draw(dummy_img)
        
        try:
            bbox = dummy_draw.textbbox((0, 0), text_str, font=font, stroke_width=stroke_w)
            left, top, right, bottom = bbox
            txt_w = right - left
            txt_h = bottom - top
        except AttributeError:
            txt_w, txt_h = dummy_draw.textsize(text_str, font=font)
            top = 0

        padding = stroke_w + 4
        txt_img_w = int(txt_w + 2 * padding)
        txt_img_h = int(txt_h + 2 * padding)

        text_card = Image.new("RGBA", (txt_img_w, txt_img_h), (0, 0, 0, 0))
        draw_card = ImageDraw.Draw(text_card)

        fill_color = (255, 255, 255, alpha)
        stroke_color = (0, 0, 0, alpha)

        draw_x = padding
        draw_y = padding - top

        try:
            draw_card.text(
                (draw_x, draw_y), 
                text_str, 
                font=font,
                fill=fill_color, 
                stroke_width=stroke_w, 
                stroke_fill=stroke_color
            )
        except TypeError:
            for dx, dy in [(-stroke_w, -stroke_w), (-stroke_w, stroke_w), (stroke_w, -stroke_w), (stroke_w, stroke_w)]:
                draw_card.text((draw_x + dx, draw_y + dy), text_str, font=font, fill=stroke_color)
            draw_card.text((draw_x, draw_y), text_str, font=font, fill=fill_color)

        if angle != 0.0:
            try:
                rotated_card = text_card.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
            except AttributeError:
                rotated_card = text_card.rotate(-angle, expand=True, resample=Image.BICUBIC)
        else:
            rotated_card = text_card

        rot_w, rot_h = rotated_card.size

        top_left_x = int(round(center_x - rot_w / 2.0))
        top_left_y = int(round(center_y - rot_h / 2.0))

        master_img.alpha_composite(rotated_card, (top_left_x, top_left_y))

    master_img.save(output_path, "PNG")

# Delegate process_video_ai to ffmpeg_service for perfect backward compatibility
from app.services.ffmpeg_service import process_video_ai
