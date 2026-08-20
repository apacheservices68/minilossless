import subprocess
import tempfile
import numpy as np
from pathlib import Path
import soundfile as sf

from scipy.io import wavfile

from app.ai.vad_detector import VADDetector
from app.core import audio_constants as const

class AudioService:
    def __init__(self):
        self.vad_detector = VADDetector()
        self.generate_default_beep()

    def generate_default_beep(self, output_path=const.DEFAULT_BEEP_PATH):
        output_path = Path(output_path)
        if output_path.is_file():
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        sample_rate = const.VAD_SAMPLE_RATE # 16000 Hz
        duration = 0.5  # seconds
        frequency = 1000  # Hz
        amplitude = 0.5 * 32767 # For 16-bit audio

        t = np.linspace(0., duration, int(sample_rate * duration), endpoint=False)
        sine_wave = amplitude * np.sin(2. * np.pi * frequency * t)

        # Convert to 16-bit PCM
        wavfile.write(output_path, sample_rate, sine_wave.astype(np.int16))
        print(f"Generated default beep sound at {output_path}")

    def extract_audio(self, video_file):
        """Extracts audio from a video file to a temporary WAV file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            output_path = tmp_file.name

        command = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-i', video_file,
            '-vn',  # No video
            '-acodec', 'pcm_s16le', # PCM 16-bit little-endian
            '-ar', str(const.VAD_SAMPLE_RATE),  # 16000 Hz
            '-ac', '1',  # Mono
            output_path
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e.stderr}")
            return None

    def optimize_intervals(self, intervals, padding, min_gap=0.15):
        """Pads and merges intervals, matching muter0.py logic."""
        if not intervals:
            return []

        # Apply padding first
        padded = [(max(0, s - padding), e + padding) for s, e in intervals]

        # Merge overlapping or close intervals
        merged = []
        if not padded:
            return []

        current_start, current_end = padded[0]

        for i in range(1, len(padded)):
            next_start, next_end = padded[i]
            if next_start - current_end < min_gap:
                # Merge
                current_end = max(current_end, next_end)
            else:
                # No merge, finalize current interval
                merged.append((current_start, current_end))
                current_start, current_end = next_start, next_end
        
        merged.append((current_start, current_end)) # Add the last interval
        return merged

    def find_speech_intervals(self, audio_path, threshold, duration_step, padding):
        """Uses VAD to find speech intervals and optimizes them."""
        # 1. Get raw intervals from VAD
        raw_intervals = self.vad_detector.find_speech_intervals(
            audio_path,
            threshold=threshold,
            duration_step=duration_step
        )

        # 2. Optimize the intervals (pad and merge)
        optimized = self.optimize_intervals(raw_intervals, padding=padding, min_gap=0.15)

        # Convert to list of dicts for compatibility with UI components
        final_intervals = [{"start": s, "end": e} for s, e in optimized]

        return final_intervals

    def generate_ffmpeg_filter_script(self, speech_intervals, total_duration):
        """Generates an FFmpeg filter script to mute SILENCE between speech intervals."""

        if not speech_intervals:
             # If no speech, mute everything
            return "volume=0"

        # Invert speech intervals to get silent intervals
        silent_intervals = []
        last_end = 0
        for segment in speech_intervals:
            start, end = segment["start"], segment["end"]
            if start > last_end:
                silent_intervals.append((last_end, start))
            last_end = end
        
        if total_duration > last_end:
            silent_intervals.append((last_end, total_duration))

        if not silent_intervals:
            return "" # No silence to mute

        # Build the filter chain to mute silent parts
        mute_chain = ",".join([
            f"volume=0:enable='between(t,{s:.3f},{e:.3f})'" 
            for s, e in silent_intervals
        ])
        
        return mute_chain

    def get_audio_duration(self, audio_path):
        """Gets the duration of an audio file in seconds."""
        try:
            info = sf.info(audio_path)
            return info.duration
        except Exception as e:
            print(f"Could not get duration of {audio_path}: {e}")
            return 0

    def generate_mute_filter_from_segments(self, segments, is_beep):
        if not segments:
            return ""

        if is_beep:
            # This part will be implemented later as per requirements for beep sound.
            # For now, just return an empty string.
            conditions = "+".join([f"between(t,{s['start']},{s['end']})" for s in segments])
            return (
                f"volume=enable='{conditions}':volume=0,"
                f"aeval='if({conditions}, sin(1000*2*PI*t)*0.3, val(0))':c=same"
            )
        else:
            return ",".join([
                const.VOLUME_MUTE_FILTER_TEMPLATE.format(start=s["start"], end=s["end"])
                for s in segments
            ])

