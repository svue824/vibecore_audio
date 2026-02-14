import sounddevice as sd
import numpy as np


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

    def is_recording(self) -> bool:
        return self._is_recording

    def play(self, data: np.ndarray, sample_rate: int):
        if len(data) == 0:
            return
        sd.play(data, samplerate=sample_rate)

    def stop(self):
        sd.stop()
