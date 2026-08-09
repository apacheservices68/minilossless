import cv2
import numpy as np
import os
from app.ai.detectors import prepare_ai_input_frame
from app.ai.processors import (
    apply_pixelate,
    apply_box_blur,
    apply_gaussian_blur,
    apply_solid_color,
    apply_replace_image,
    blur_background
)

class AIPipeline:
    """
    A wrapper class that connects detectors and processors to process individual frames.
    """
    def __init__(self, detector=None, segmenter=None):
        self.detector = detector
        self.segmenter = segmenter

    def process_frame(
        self,
        frame: np.ndarray,
        face_blur_enabled: bool,
        face_blur_pct: float,
        face_blur_type: str,
        face_blur_image_path: str,
        face_blur_style: str,
        face_blur_strength: int,
        bg_blur_enabled: bool,
        bg_blur_strength: int
    ) -> np.ndarray:
        """
        Process a single frame with background blur and face blur options.
        """
        processed_frame = frame.copy()
        height, width = frame.shape[:2]

        # 1. Background Blur
        if bg_blur_enabled and self.segmenter is not None:
            mp_image, sx, sy = prepare_ai_input_frame(processed_frame)
            segmentation_result = self.segmenter.segment(mp_image)
            category_mask = segmentation_result.category_mask.numpy_view()
            category_mask = np.squeeze(category_mask)
            processed_frame = blur_background(processed_frame, category_mask, bg_blur_strength)

        # 2. Face Blur
        if face_blur_enabled and self.detector is not None:
            mp_image, sx, sy = prepare_ai_input_frame(processed_frame)
            detection_result = self.detector.detect(mp_image)
            
            for detection in detection_result.detections:
                bbox = detection.bounding_box
                
                ow = int(bbox.width * sx)
                oh = int(bbox.height * sy)
                
                # Alignment and scaling shift adjustments (verbatim from the legacy codebase)
                shift_up = int(oh * 0.20)
                shift_left = int(ow * 0.05)
                
                h_adjusted = int(oh * 1.25)
                w_adjusted = int(ow * 1.10)
                
                xmin = max(0, int(bbox.origin_x * sx) - shift_left)
                ymin = max(0, int(bbox.origin_y * sy) - shift_up)
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
                        style = face_blur_style.lower() if isinstance(face_blur_style, str) else "gaussian"
                        strength = max(1, int(face_blur_strength))
                        
                        # Apply effect style
                        if style == "pixel":
                            blurred_roi = apply_pixelate(face_roi, strength)
                        elif style == "box":
                            blurred_roi = apply_box_blur(face_roi, strength)
                        elif style == "blackout":
                            blurred_roi = apply_solid_color(face_roi)
                        else:  # gaussian
                            blurred_roi = apply_gaussian_blur(face_roi, strength)
                        
                        # Apply shape / mask type
                        if face_blur_type == "Ellipse":
                            mask = np.zeros((blur_h, w), dtype=np.uint8)
                            center = (w // 2, blur_h // 2)
                            axes = (w // 2, blur_h // 2)
                            cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
                            
                            mask_ksize = max(5, int(min(w, blur_h) * 0.20) | 1)
                            mask_blurred = cv2.GaussianBlur(mask, (mask_ksize, mask_ksize), 0) / 255.0
                            mask_3d = np.atleast_3d(mask_blurred)
                            
                            blended_roi = (blurred_roi * mask_3d + face_roi * (1.0 - mask_3d)).astype(np.uint8)
                            processed_frame[ymin:ymin + blur_h, xmin:xmin + w] = blended_roi
                            
                        elif face_blur_type == "Image" and face_blur_image_path and os.path.exists(face_blur_image_path):
                            processed_frame[ymin:ymin + blur_h, xmin:xmin + w] = apply_replace_image(face_roi, face_blur_image_path)
                        else:
                            # Square blur (Default)
                            processed_frame[ymin:ymin + blur_h, xmin:xmin + w] = blurred_roi

        return processed_frame
