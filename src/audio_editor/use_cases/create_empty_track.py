from audio_editor.domain.audio_track import AudioTrack
import numpy as np


class CreateEmptyTrack:
    """
    Use case for creating a new empty audio track.
    This class produces a valid AudioTrack object with initialized data.
    """

    def execute(self, name: str, duration_seconds: float, sample_rate: int) -> AudioTrack:
        """
        Create an empty AudioTrack.

        Args:
            name (str): Name of the new track.
            duration_seconds (float): Duration of the track in seconds.
            sample_rate (int): Number of samples per second (Hz).

        Returns:
            AudioTrack: A new AudioTrack instance with zeros as waveform data.
        """

        # Validate input
        if duration_seconds <= 0:
            raise ValueError("Duration must be greater than zero.")
        if sample_rate <= 0:
            raise ValueError("Sample rate must be greater than zero.")

        # Calculate total number of samples: duration * sample_rate
        total_samples = int(duration_seconds * sample_rate)

        # Create waveform data as a NumPy array of zeros (float32)
        # np.zeros creates an n-dimensional array filled with zeros
        # float32 is standard for audio samples to save memory
        data = np.zeros(total_samples, dtype=np.float32)

        # Create and return the AudioTrack object
        return AudioTrack(
            name=name,
            sample_rate=sample_rate,
            data=data
        )
