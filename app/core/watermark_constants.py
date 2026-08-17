# Added on 08132026: [VI] Dinh nghia cac vi tri watermark cho FFMPEG / [EN] Define watermark positions for FFmpeg
# WATERMARK_POSITIONS = {
#     "Top Left": "x=10:y=10",
#     "Top Right": "x=W-w-10:y=10",
#     "Bottom Left": "x=10:y=H-overlay_h-10",
#     "Bottom Right": "x=W-w-10:y=H-overlay_h-10",
#     "Top Center": "x=(W-w)/2:y=10",
#     "Bottom Center": "x=(W-w)/2:y=H-overlay_h-10",
#     "Middle Left": "x=10:y=(H-overlay_h)/2",
#     "Middle Right": "x=W-w-10:y=(H-overlay_h)/2",
# }

WATERMARK_POSITIONS = {
    "top_left": {
        "label": "Top Left",
        "expr": "x=10:y=10"
    },
    "top_right": {
        "label": "Top Right",
        "expr": "x=W-w-10:y=10"
    },
    "bottom_left": {
        "label": "Bottom Left",
        "expr": "x=10:y=H-h-10"
    },
    "bottom_right": {
        "label": "Bottom Right",
        "expr": "x=W-w-10:y=H-h-10"
    },
    "top_center": {
        "label": "Top Center",
        "expr": "x=(W-w)/2:y=10"
    },
    "bottom_center": {
        "label": "Bottom Center",
        "expr": "x=(W-w)/2:y=H-h-10"
    },
    "middle_left": {
        "label": "Middle Left",
        "expr": "x=10:y=(H-h)/2"
    },
    "middle_right": {
        "label": "Middle Right",
        "expr": "x=W-w-10:y=(H-h)/2"
    }
}

DEFAULT_FONT_PATH = "assets/fonts/DejaVuSans-Bold.ttf"
DEFAULT_FONT_FAMILY = "DejaVu Sans"
DEFAULT_VIDEO_WIDTH = 1280
DEFAULT_VIDEO_HEIGHT = 720
