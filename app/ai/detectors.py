import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from app.core.constants import FACE_MODEL_PATH, SELFIE_MODEL_PATH, AI_IMAGE_SIZE

def get_face_detector():
    """
    Initialize and return MediaPipe FaceDetector using CPU delegate.
    """
    model_p = FACE_MODEL_PATH if os.path.exists(FACE_MODEL_PATH) else "face_detector.tflite"
    if os.path.exists(model_p):
        base_options = python.BaseOptions(
            model_asset_path=model_p,
            delegate=python.BaseOptions.Delegate.CPU
        )
        options = vision.FaceDetectorOptions(base_options=base_options)
        return vision.FaceDetector.create_from_options(options)
    return None

def get_selfie_segmenter():
    """
    Initialize and return MediaPipe ImageSegmenter (Selfie) using CPU delegate.
    """
    model_p = SELFIE_MODEL_PATH if os.path.exists(SELFIE_MODEL_PATH) else "selfie_segmenter.tflite"
    if os.path.exists(model_p):
        base_options = python.BaseOptions(
            model_asset_path=model_p,
            delegate=python.BaseOptions.Delegate.CPU
        )
        options = vision.ImageSegmenterOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            output_category_mask=True
        )
        return vision.ImageSegmenter.create_from_options(options)
    return None

def prepare_ai_input_frame(frame: np.ndarray) -> tuple[mp.Image, float, float]:
    """
    Resize BGR frame to 320x320, convert to RGB, create mp.Image.
    Returns (mp_image, sx, sy) where sx, sy are scale factors to map back coordinates.
    """
    height, width = frame.shape[:2]
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized_rgb = cv2.resize(rgb_frame, (AI_IMAGE_SIZE, AI_IMAGE_SIZE))
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=resized_rgb)
    sx = width / float(AI_IMAGE_SIZE)
    sy = height / float(AI_IMAGE_SIZE)
    return mp_image, sx, sy
