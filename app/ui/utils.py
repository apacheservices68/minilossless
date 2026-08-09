import os
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtMultimedia import QMediaPlayer
import app.services.ffmpeg_service as ffmpeg_service

def toggle_play_pause(player: QMediaPlayer, btn_play_pause) -> str:
    """Toggles play/pause state of QMediaPlayer and updates the button text."""
    if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
        player.pause()
        new_text = "Play"
    else:
        player.play()
        new_text = "Pause"
    btn_play_pause.setText(new_text)
    return new_text

def get_formatted_time_str(pos_ms: float, dur_ms: float) -> str:
    """Formats millisecond positions and durations into standard time format string."""
    pos_sec = pos_ms / 1000.0
    dur_sec = dur_ms / 1000.0
    pos_str = ffmpeg_service.format_seconds_to_time(pos_sec)
    dur_str = ffmpeg_service.format_seconds_to_time(dur_sec)
    return f"{pos_str} / {dur_str}"

def handle_player_position_changed(slider, is_slider_moving: bool, position: int, update_time_cb):
    """Updates slider and time label when player position changes."""
    if not is_slider_moving:
        slider.setValue(position)
    update_time_cb()

def handle_player_duration_changed(slider, duration: int, update_time_cb):
    """Updates slider range and time label when player duration changes."""
    slider.setRange(0, duration)
    update_time_cb()

def show_close_video_help(parent):
    """Displays a standard messagebox explaining how to close the video."""
    QMessageBox.information(
        parent,
        "Trợ giúp",
        "Nhấn Ctrl + W (Windows/Linux) hoặc Cmd + W (macOS) để đóng video hiện tại."
    )
