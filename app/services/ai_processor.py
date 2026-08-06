import math
import os
import sys
import cv2
import numpy as np
import subprocess
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtCore import QObject, pyqtSignal

# Lấy thư mục chứa file ai_processor.py (app/services)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Lùi lại 2 cấp để về đúng root project (/home/apache/code/py/lossless)
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
FACE_MODEL_PATH = os.path.join(BASE_DIR, "face_detector.tflite")
SELFIE_MODEL_PATH = os.path.join(BASE_DIR, "selfie_segmenter.tflite")

class AIProcessorSignals(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

def create_advanced_watermark_image(width: int, height: int, texts: list, output_path: str, *args, **kwargs):
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

        # Font size chuẩn
        base_font_size = float(item["rel_font_size"]) * diag
        font_size = max(10, int(round(base_font_size * 1.3333)))

        # Stroke width
        if "stroke_width" in item and item["stroke_width"] is not None:
            stroke_w = int(item["stroke_width"])
        else:
            stroke_w = max(1, int(font_size // 25))
        
        angle = float(item.get("rotation_angle", 0))

        # --- FIX OPACITY CHUẨN ĐÉT AT ANY FORMAT ---
        raw_opacity = item.get("opacity", 1.0)
        try:
            opacity_val = float(raw_opacity)
            # Nếu UI gửi scale 0 - 100 (ví dụ 30%), tự quy đổi về 0.3
            if opacity_val > 1.0:
                opacity_val = opacity_val / 100.0
        except (ValueError, TypeError):
            opacity_val = 1.0

        opacity_val = max(0.0, min(1.0, opacity_val))
        alpha = int(round(opacity_val * 255))

        # Font path
        font_path = os.path.join(BASE_DIR, "assets", "fonts", "DejaVuSans-Bold.ttf")
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
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

        # Áp alpha cho cả fill và stroke
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
    signals: AIProcessorSignals = None,
    preview_width=0, 
    preview_height=0,
    progress_callback = None,
    *args,    
    **kwargs
):
    input_video_path = input_video_path or kwargs.get('input_path')
    output_video_path = output_video_path or kwargs.get('output_path')
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

    temp_watermark_path = os.path.join(BASE_DIR, "temp_wm.png")
    detector = None
    segmenter = None
    
    if face_blur_enabled or bg_blur_enabled:
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        if face_blur_enabled:
            model_p = FACE_MODEL_PATH if os.path.exists(FACE_MODEL_PATH) else "face_detector.tflite"
            if os.path.exists(model_p):
                base_options = python.BaseOptions(model_asset_path=model_p)
                options = vision.FaceDetectorOptions(base_options=base_options)
                detector = vision.FaceDetector.create_from_options(options)
            
        if bg_blur_enabled:
            model_p = SELFIE_MODEL_PATH if os.path.exists(SELFIE_MODEL_PATH) else "selfie_segmenter.tflite"
            if os.path.exists(model_p):
                base_options = python.BaseOptions(model_asset_path=model_p)
                options = vision.ImageSegmenterOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.IMAGE,
                    output_category_mask=True
                )
                segmenter = vision.ImageSegmenter.create_from_options(options)

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
            create_advanced_watermark_image(
                width, height, texts, temp_watermark_path, 
                preview_width=preview_width, 
                preview_height=preview_height
            )
        
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}",
            "-r", f"{fps}",
            "-i", "-", 
            "-i", temp_watermark_path,
            "-i", input_video_path,
            "-filter_complex", "[0:v][1:v]overlay=0:0[outv]",
            "-map", "[outv]",
            "-map", "2:a?",
        ]
        
        if use_cuda:
            ffmpeg_cmd.extend([
                "-c:v", "h264_nvenc",
                "-preset", "p4",
                "-pix_fmt", "yuv420p"
            ])
        else:
            ffmpeg_cmd.extend([
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-pix_fmt", "yuv420p"
            ])
            
        ffmpeg_cmd.append(output_video_path)
        
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

            processed_frame = frame.copy()
            
            # --- 1. BACKGROUND BLUR ---
            if bg_blur_enabled and segmenter is not None:
                rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                segmentation_result = segmenter.segment(mp_image)
                category_mask = segmentation_result.category_mask.numpy_view()
                category_mask = np.squeeze(category_mask)
                
                if category_mask.shape[:2] != (height, width):
                    category_mask = cv2.resize(category_mask.astype(np.float32), (width, height), interpolation=cv2.INTER_LINEAR)
                
                raw_mask = (category_mask == 0).astype(np.float32)
                smooth_mask = cv2.GaussianBlur(raw_mask, (21, 21), 0)
                fg_mask_3d = np.atleast_3d(smooth_mask)
                
                ksize = int(bg_blur_strength)
                if ksize % 2 == 0:
                    ksize += 1
                ksize = max(1, ksize)
                blurred_frame = cv2.GaussianBlur(processed_frame, (ksize, ksize), 0)
                
                processed_frame = (processed_frame * fg_mask_3d + blurred_frame * (1.0 - fg_mask_3d)).astype(np.uint8)
                
            # --- 2. FACE BLUR ---
            if face_blur_enabled and detector is not None:
                rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                detection_result = detector.detect(mp_image)
                
                for detection in detection_result.detections:
                    bbox = detection.bounding_box
                    
                    ow = int(bbox.width)
                    oh = int(bbox.height)
                    
                    # Tinh toan dich chuyen va mo rong de khac phuc lech tam va ho vung tran
                    # Dich len tren 20% chieu cao (giup che vung tran/toc)
                    shift_up = int(oh * 0.20)
                    # Dich sang trai 5% chieu rong de can xunh lai tam (khac phuc lech phai nhe)
                    shift_left = int(ow * 0.05)
                    
                    # Chieu cao tang 25% de bo tron phan tran/toc phia tren va cam phia duoi
                    h_adjusted = int(oh * 1.25)
                    # Chieu rong tang 10% de che phu het ma/tai
                    w_adjusted = int(ow * 1.10)
                    
                    xmin = max(0, int(bbox.origin_x) - shift_left)
                    ymin = max(0, int(bbox.origin_y) - shift_up)
                    w = min(width - xmin, w_adjusted)
                    h = min(height - ymin, h_adjusted)
                    
                    if w > 0 and h > 0:
                        if face_blur_pct <= 0.0:
                            blur_h = h
                        else:
                            blur_h = int(h * (face_blur_pct / 100.0))
                            blur_h = max(1, min(h, blur_h))
                            
                        blur_h = min(height - ymin, blur_h)
                        
                        if blur_h > 0 and w > 0:
                            face_roi = processed_frame[ymin:ymin + blur_h, xmin:xmin + w]
                            
                            # Xác định blurred_roi dựa trên face_blur_style và face_blur_strength
                            style = face_blur_style.lower() if isinstance(face_blur_style, str) else "gaussian"
                            strength = max(1, int(face_blur_strength))
                            
                            if style == "pixel":
                                # Pixelate
                                small_w = max(1, w // strength)
                                small_h = max(1, blur_h // strength)
                                temp = cv2.resize(face_roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
                                blurred_roi = cv2.resize(temp, (w, blur_h), interpolation=cv2.INTER_NEAREST)
                            elif style == "box":
                                # Box Blur
                                face_ksize = strength
                                if face_ksize % 2 == 0:
                                    face_ksize += 1
                                face_ksize = max(1, face_ksize)
                                blurred_roi = cv2.blur(face_roi, (face_ksize, face_ksize))
                            elif style == "blackout":
                                # Blackout
                                blurred_roi = np.zeros_like(face_roi)
                            else:  # Gaussian
                                face_ksize = strength
                                if face_ksize % 2 == 0:
                                    face_ksize += 1
                                face_ksize = max(1, face_ksize)
                                blurred_roi = cv2.GaussianBlur(face_roi, (face_ksize, face_ksize), 0)
                            
                            if face_blur_type == "Ellipse":
                                # Vẽ mặt nạ elip mềm mại ôm sát khuôn mặt
                                mask = np.zeros((blur_h, w), dtype=np.uint8)
                                center = (w // 2, blur_h // 2)
                                axes = (w // 2, blur_h // 2)
                                cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
                                
                                # Tạo viền mờ mềm mại cho mặt nạ
                                mask_ksize = max(5, int(min(w, blur_h) * 0.20) | 1)
                                mask_blurred = cv2.GaussianBlur(mask, (mask_ksize, mask_ksize), 0) / 255.0
                                mask_3d = np.atleast_3d(mask_blurred)
                                
                                blended_roi = (blurred_roi * mask_3d + face_roi * (1.0 - mask_3d)).astype(np.uint8)
                                processed_frame[ymin:ymin + blur_h, xmin:xmin + w] = blended_roi
                                
                            elif face_blur_type == "Image" and face_blur_image_path and os.path.exists(face_blur_image_path):
                                replacement_img = cv2.imread(face_blur_image_path, cv2.IMREAD_UNCHANGED)
                                if replacement_img is not None:
                                    resized_replacement = cv2.resize(replacement_img, (w, blur_h))
                                    if resized_replacement.shape[2] == 4:
                                        alpha_channel = resized_replacement[:, :, 3] / 255.0
                                        alpha_mask = np.atleast_3d(alpha_channel)
                                        rgb_replacement = resized_replacement[:, :, :3]
                                        
                                        blended = (rgb_replacement * alpha_mask + face_roi * (1.0 - alpha_mask)).astype(np.uint8)
                                        processed_frame[ymin:ymin + blur_h, xmin:xmin + w] = blended
                                    else:
                                        processed_frame[ymin:ymin + blur_h, xmin:xmin + w] = resized_replacement
                                else:
                                    # Fallback
                                    processed_frame[ymin:ymin + blur_h, xmin:xmin + w] = blurred_roi
                            else:
                                # Square blur (Default)
                                processed_frame[ymin:ymin + blur_h, xmin:xmin + w] = blurred_roi
                            
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