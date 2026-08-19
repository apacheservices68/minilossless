'''Manages configuration constants for the Audio Processing Tab.'''

# VAD (Voice Activity Detection) AI Model Constants
THRESHOLD_MIN = 0.0
THRESHOLD_MAX = 1.0
THRESHOLD_DEFAULT = 0.5

DURATION_MIN = 0.0
DURATION_MAX = 10.0
DURATION_DEFAULT = 1.0

PADDING_MIN = 0.0
PADDING_MAX = 5.0
PADDING_DEFAULT = 0.2

# Resource Management
MAX_BEEP_FILE_SIZE_MB = 1.0

# Paths and Remote URLs
VAD_MODEL_PATH = "assets/models/silero_vad.onnx"
DEFAULT_BEEP_PATH = "assets/audio/beep_default.wav"

# Fallback download links
VAD_MODEL_URL = "https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.onnx"
BEEP_AUDIO_URL = "https://github.com/apacheservices68/minilossless-assets/raw/main/beep_default.wav"

# FFmpeg Command Templates and Filters
# These will be defined later as the implementation progresses
FFMPEG_EXTRACT_AUDIO_TEMPLATE = '''ffmpeg -i "{input_file}" -vn -ar 16000 -ac 1 "{output_file}"'''

FFMPEG_MUTED_FILTER_STRING = "volume=0"
