from dataclasses import dataclass
from pathlib import Path
import numpy as np


@dataclass
class AudioTrack:
    """ 
    Core domain entity representing an audio track.
    Holds name, sample_rate, waveform data, and optional file path.
    """
    name: str
    sample_rate: int
    data: np.ndarray
    file_path: Path | None = None

    @property
    def duration_seconds(self) -> float:
        """Return the duration of the track in seconds."""
        if self.sample_rate == 0:
            return 0.0
        return len(self.data) / self.sample_rate

    def rename(self, new_name: str) -> None:
        """Rename the track."""
        if not new_name.strip():
            raise ValueError("Track name cannot be empty.")
        self.name = new_name
