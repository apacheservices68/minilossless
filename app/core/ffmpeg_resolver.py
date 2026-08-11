'''Module to resolve the path to ffmpeg and ffprobe.'''
import sys
import shutil
from pathlib import Path

def get_ffmpeg_path():
    '''Resolves the path to the ffmpeg executable.

    The lookup order is:
    1. assets/bin/ directory relative to the executable (for PyInstaller).
    2. System's PATH.

    Returns:
        str: The path to the ffmpeg executable or None if not found.
    '''
    # For PyInstaller
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys._MEIPASS)
    else:
        app_dir = Path(__file__).resolve().parents[2]

    ffmpeg_in_assets = app_dir / "assets" / "bin" / "ffmpeg"
    if ffmpeg_in_assets.exists():
        return str(ffmpeg_in_assets)

    return shutil.which('ffmpeg')

def get_ffprobe_path():
    '''Resolves the path to the ffprobe executable.

    The lookup order is:
    1. assets/bin/ directory relative to the executable (for PyInstaller).
    2. System's PATH.

    Returns:
        str: The path to the ffprobe executable or None if not found.
    '''
    # For PyInstaller
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys._MEIPASS)
    else:
        app_dir = Path(__file__).resolve().parents[2]

    ffprobe_in_assets = app_dir / "assets" / "bin" / "ffprobe"
    if ffprobe_in_assets.exists():
        return str(ffprobe_in_assets)

    return shutil.which('ffprobe')
