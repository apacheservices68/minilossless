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

# FFmpeg constants
class VIDEO_CODECS:
    CPU_H264 = "libx264"
    NVENC_H264 = "h264_nvenc"
    NVENC_HEVC = "hevc_nvenc"
    QSV_H264 = "h264_qsv"
    AMF_H264 = "h264_amf"
    VAAPI_H264 = "h264_vaapi"
    AAC = "aac"
    PNG = "png"
    MJPEG = "mjpeg"

class IMAGE_FORMATS:
    IMAGE2 = "image2"

class HW_ACCELS:
    CUDA = "cuda"
    AUTO = "auto"

class FFMPEG_COMMANDS:
    INPUT = "-i"
    OVERWRITE_OUTPUT = "-y"
    SEEK = "-ss"
    TO = "-to"
    VIDEO_FILTER = "-vf"
    AUDIO_FILTER = "-af"
    COPY_CODEC = "-c"
    VIDEO_CODEC = "-c:v"
    AUDIO_CODEC = "-c:a"
    PRESET = "-preset"
    AUDIO_BITRATE = "-b:a"
    CONSTANT_RATE_FACTOR = "-crf"
    PIXEL_FORMAT = "-pix_fmt"
    FRAMES_VIDEO = "-frames:v"
    QUALITY = "-q:v"
    MAP = "-map"
    METADATA = "-metadata"
    MAP_METADATA = "-map_metadata"
    FRAME_RATE = "-r"

class FFMPEG_FLAGS:
    AVOID_NEGATIVE_TS = "-avoid_negative_ts"
    FASTSTART = "+faststart"
    MAKE_ZERO = "make_zero"
    SET_PTS_TO_START = "setpts=PTS-STARTPTS"
    ASET_PTS_TO_START = "asetpts=PTS-STARTPTS"
    CONCAT = "concat"
    SAFE = "-safe"

class PIXEL_FORMATS:
    YUV420P = "yuv420p"
    BGR24 = "bgr24"
