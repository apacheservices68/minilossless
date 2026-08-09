import os
import urllib.request
from app.core.constants import BASE_DIR

MODELS_DIR = os.path.join(BASE_DIR, "assets", "models")

ASSETS = {
    "face_detector.tflite": "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
    "selfie_segmenter.tflite": "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"
}

def ensure_assets_exist():
    """
    Ensure required AI models exist in assets/models/.
    If they do not exist, download them from official sources.
    If they exist, bypass download immediately for quick startup.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    for filename, url in ASSETS.items():
        file_path = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(file_path):
            print(f"[Asset Manager] Downloading {filename} to {file_path}...")
            try:
                urllib.request.urlretrieve(url, file_path)
                print(f"[Asset Manager] Successfully downloaded {filename}")
            except Exception as e:
                print(f"[Asset Manager] Error downloading {filename}: {e}")
                raise e
