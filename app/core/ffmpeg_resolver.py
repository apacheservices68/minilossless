'''Module to resolve the path to ffmpeg and ffprobe across platforms.'''
import sys
import os
import shutil
import platform
from pathlib import Path

def get_base_dir() -> Path:
    """Xác định gốc thư mục dự án."""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parents[2]

def _setup_library_paths(bin_dir: Path):
    """Cấu hình biến môi trường nạp thư viện động cho mọi hệ điều hành."""
    bin_str = str(bin_dir.resolve())
    current_os = platform.system()

    if current_os == "Linux":
        # Nạp thư viện .so trên Linux
        current_ld = os.environ.get("LD_LIBRARY_PATH", "")
        if bin_str not in current_ld:
            os.environ["LD_LIBRARY_PATH"] = f"{bin_str}:{current_ld}" if current_ld else bin_str

    elif current_os == "Darwin":
        # Nạp thư viện .dylib trên macOS
        current_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
        if bin_str not in current_dyld:
            os.environ["DYLD_LIBRARY_PATH"] = f"{bin_str}:{current_dyld}" if current_dyld else bin_str

    elif current_os == "Windows":
        # Nạp thư viện .dll trên Windows bằng cách đưa vào PATH
        current_path = os.environ.get("PATH", "")
        if bin_str not in current_path:
            os.environ["PATH"] = f"{bin_str};{current_path}" if current_path else bin_str

def get_ffmpeg_path() -> str:
    """Trả về đường dẫn tới ffmpeg và tự động cấu hình môi trường thư viện động."""
    base_dir = get_base_dir()
    exec_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    
    bin_dir = base_dir / "assets" / "bin"
    ffmpeg_in_assets = bin_dir / exec_name
    
    if ffmpeg_in_assets.exists():
        _setup_library_paths(bin_dir)
        return str(ffmpeg_in_assets)

    system_ffmpeg = shutil.which(exec_name)
    if system_ffmpeg:
        return system_ffmpeg
        
    return exec_name

def get_ffprobe_path() -> str:
    """Trả về đường dẫn tới ffprobe và tự động cấu hình môi trường thư viện động."""
    base_dir = get_base_dir()
    exec_name = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
    
    bin_dir = base_dir / "assets" / "bin"
    ffprobe_in_assets = bin_dir / exec_name
    
    if ffprobe_in_assets.exists():
        _setup_library_paths(bin_dir)
        return str(ffprobe_in_assets)

    system_ffprobe = shutil.which(exec_name)
    if system_ffprobe:
        return system_ffprobe
        
    return exec_name