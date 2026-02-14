import sounddevice as sd
import numpy as np


class AudioEngine:
    def __init__(self):
        self.stream = None

    # ---- Playback ----
    def play(self, data: np.ndarray, sample_rate: int):
        if len(data) == 0:
            return
        sd.play(data, samplerate=sample_rate)

    def stop(self):
        sd.stop()

    # ---- Recording ----
    def record(self, duration_seconds: int, sample_rate: int):
        recording = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32"
        )
        sd.wait()
        return recording.flatten()
