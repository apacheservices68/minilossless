import os
import onnxruntime
import urllib.request
from pathlib import Path
import numpy as np
import soundfile as sf

from app.core import audio_constants as const

class VADDetector:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.ensure_assets()

        # Initialize ONNX runtime session
        self.session = onnxruntime.InferenceSession(const.VAD_MODEL_PATH)
        self.session.intra_op_num_threads = 1 # Recommended for performance

        self.reset_states()

    def reset_states(self):
        """Reset the state of the VAD model"""
        input_names = [inp.name for inp in self.session.get_inputs()]
        if 'state' in input_names:
            self._state = np.zeros((2, 1, 128), dtype=np.float32)
        else: # Legacy h, c states
            self._h = np.zeros((2, 1, 64), dtype=np.float32)
            self._c = np.zeros((2, 1, 64), dtype=np.float32)
            self._state = None # Explicitly set to None

    def ensure_assets(self):
        """Check for model and audio files, download if they don't exist."""
        model_path = Path(const.VAD_MODEL_PATH)
        if not model_path.is_file():
            model_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Downloading VAD model to {const.VAD_MODEL_PATH}...")
            urllib.request.urlretrieve(const.VAD_MODEL_URL, const.VAD_MODEL_PATH)
            print("Download complete.")

    def find_speech_intervals(self, audio_path, threshold, duration_step=0.1):
        """
        Detects speech intervals using ONNX runtime, matching muter0.py logic.
        """
        try:
            wav, sr = sf.read(audio_path, dtype='float32')
            if sr != const.VAD_SAMPLE_RATE:
                # This should be handled by ffmpeg extraction, but as a fallback
                raise ValueError(f"Expected {const.VAD_SAMPLE_RATE}Hz, got {sr}")
            if wav.ndim > 1:
                wav = np.mean(wav, axis=1) # Stereo to mono
        except Exception as e:
            print(f"Error reading audio file: {e}")
            return []

        # Normalize audio
        wav = wav / (np.max(np.abs(wav)) + 1e-7)

        self.reset_states()
        input_names = [inp.name for inp in self.session.get_inputs()]

        step_samples = int(duration_step * const.VAD_SAMPLE_RATE)
        window_size_samples = 512 # As per muter0.py logic
        raw_intervals = []

        for start in range(0, len(wav), step_samples):
            end = start + step_samples
            chunk = wav[start:end]
            
            max_prob_in_chunk = 0.0
            
            # Process chunk in smaller windows for VAD
            for i in range(0, len(chunk), window_size_samples):
                window = chunk[i : i + window_size_samples]
                if len(window) < window_size_samples:
                    window = np.pad(window, (0, window_size_samples - len(window)))
                
                window = window.reshape(1, -1)

                # Prepare ONNX inputs
                ort_inputs = {'input': window}
                sr_tensor = np.array(const.VAD_SAMPLE_RATE, dtype=np.int64)
                
                if 'sr' in input_names:
                    ort_inputs['sr'] = sr_tensor
                
                if self._state is not None and 'state' in input_names:
                    ort_inputs['state'] = self._state
                elif 'h' in input_names and 'c' in input_names:
                    ort_inputs['h'] = self._h
                    ort_inputs['c'] = self._c

                # Run inference
                ort_outs = self.session.run(None, ort_inputs)
                prob = ort_outs[0].item()

                # Update state
                if 'state' in input_names and len(ort_outs) > 1:
                    self._state = ort_outs[1]
                elif 'h' in input_names and 'c' in input_names:
                    self._h, self._c = ort_outs[1], ort_outs[2]
                
                if prob > max_prob_in_chunk:
                    max_prob_in_chunk = prob
            
            if max_prob_in_chunk > threshold:
                interval_end = min(end, len(wav)) / const.VAD_SAMPLE_RATE
                interval_start = start / const.VAD_SAMPLE_RATE
                raw_intervals.append((interval_start, interval_end))
                
        return raw_intervals

    def detect_speech(self, audio_data, sample_rate):
        # This method can be deprecated or refactored to use find_speech_intervals
        # For now, let's keep it as a placeholder to avoid breaking other parts of the code
        # that might be calling it. In a real scenario, we'd refactor this.
        print("VAD speech detection logic has been moved to find_speech_intervals.")
        # Or, adapt find_speech_intervals to work with in-memory data
        return []
