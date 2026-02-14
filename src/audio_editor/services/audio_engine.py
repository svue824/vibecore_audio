import sounddevice as sd
import numpy as np
from typing import List

class AudioEngine:
    def __init__(self):
        self._input_stream = None
        self._recording_buffer = []
        self._is_recording = False

    def start_recording(self, sample_rate: int):
        if self._is_recording:
            return

        self._recording_buffer = []
        self._is_recording = True

        def callback(indata, frames, time, status):
            if status:
                print(status)
            # Keep callback lightweight
            self._recording_buffer.append(indata.copy())

        self._input_stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            callback=callback,
        )

        self._input_stream.start()

    def stop_recording(self) -> np.ndarray:
        if not self._is_recording:
            return np.array([], dtype="float32")

        self._input_stream.stop()
        self._input_stream.close()

        self._is_recording = False

        if not self._recording_buffer:
            return np.array([], dtype="float32")

        audio = np.concatenate(self._recording_buffer, axis=0)
        return audio.flatten()

    def get_recording_preview(self) -> np.ndarray:
        """Return currently buffered recording audio without stopping the stream."""
        if not self._recording_buffer:
            return np.array([], dtype="float32")
        try:
            audio = np.concatenate(list(self._recording_buffer), axis=0)
        except ValueError:
            return np.array([], dtype="float32")
        return audio.flatten()

    def is_recording(self) -> bool:
        return self._is_recording

    def play(self, data: np.ndarray, sample_rate: int):
        if len(data) == 0:
            return
        sd.play(data, samplerate=sample_rate)

    def stop(self):
        sd.stop()

    def play_project(self, tracks: List):
        """
        Mix all tracks together and play as a single audio stream.
        Handles different lengths by padding shorter tracks.
        """
        if not tracks:
            return

        # Find max length
        max_length = max((len(t.data) for t in tracks if len(t.data) > 0), default=0)

        if max_length == 0:
            return

        # Initialize mix
        mix = np.zeros(max_length, dtype=np.float32)

        # Sum tracks
        for t in tracks:
            if len(t.data) == 0 or t.muted:
                continue
            track_data = np.array(t.data, dtype=np.float32)
            track_data *= t.volume  # Apply volume
            # Pad if shorter
            if len(track_data) < max_length:
                track_data = np.pad(track_data, (0, max_length - len(track_data)))
            mix += track_data

        # Normalize to avoid clipping
        max_val = np.max(np.abs(mix))
        if max_val > 1.0:
            mix = mix / max_val

        sd.play(mix, samplerate=tracks[0].sample_rate)
