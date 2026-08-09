import os

# Base directory of the project
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

# AI pipeline constants
AI_IMAGE_SIZE = 320

# Default path for models
FACE_MODEL_PATH = os.path.join(BASE_DIR, "assets", "models", "face_detector.tflite")
SELFIE_MODEL_PATH = os.path.join(BASE_DIR, "assets", "models", "selfie_segmenter.tflite")

# Font paths
DEFAULT_FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "DejaVuSans-Bold.ttf")

# Default UI properties
DEFAULT_FONT_SIZE = 32
DEFAULT_OPACITY = 100
DEFAULT_ROTATION = 0
DEFAULT_FACE_BLUR_STRENGTH = 15
DEFAULT_BG_BLUR_STRENGTH = 101
