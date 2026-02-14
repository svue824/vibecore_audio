from dataclasses import dataclass, field
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
    volume: float = 1.0  # 100% by default
    muted: bool = False
    sample_boundaries: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.set_data(self.data, reset_boundaries=True)

    def set_data(self, data: np.ndarray, reset_boundaries: bool = True) -> None:
        arr = np.asarray(data, dtype=np.float32).flatten()
        self.data = arr
        if reset_boundaries:
            self.sample_boundaries = [len(arr)] if len(arr) > 0 else []
        else:
            self._normalize_boundaries()

    def append_data(self, data: np.ndarray, as_new_segment: bool = True) -> None:
        incoming = np.asarray(data, dtype=np.float32).flatten()
        if incoming.size == 0:
            return

        current = np.asarray(self.data, dtype=np.float32).flatten()
        prev_len = len(current)
        self.data = np.concatenate([current, incoming])

        if as_new_segment:
            if prev_len > 0 and prev_len not in self.sample_boundaries:
                self.sample_boundaries.append(prev_len)
            self.sample_boundaries.append(len(self.data))
        else:
            if self.sample_boundaries:
                self.sample_boundaries[-1] = len(self.data)
            else:
                self.sample_boundaries = [len(self.data)]

        self._normalize_boundaries()

    def split_sample_at(self, sample_index: int) -> bool:
        if len(self.data) < 2:
            return False
        idx = int(np.clip(sample_index, 0, len(self.data)))
        if idx <= 0 or idx >= len(self.data):
            return False
        if idx in self.sample_boundaries:
            return False

        self.sample_boundaries.append(idx)
        self._normalize_boundaries()
        return True

    def nearest_boundary(self, sample_index: int) -> int:
        idx = int(np.clip(sample_index, 0, len(self.data)))
        candidates = [0, *self.sample_boundaries]
        return min(candidates, key=lambda boundary: abs(boundary - idx))

    def next_boundary_after(self, sample_index: int) -> int:
        idx = int(np.clip(sample_index, 0, len(self.data)))
        for boundary in self.sample_boundaries:
            if boundary > idx:
                return boundary
        return len(self.data)

    def previous_boundary_before(self, sample_index: int) -> int:
        idx = int(np.clip(sample_index, 0, len(self.data)))
        prev = 0
        for boundary in self.sample_boundaries:
            if boundary >= idx:
                return prev
            prev = boundary
        return prev

    def cut_range(self, start_index: int, end_index: int) -> bool:
        if len(self.data) == 0:
            return False

        start = int(np.clip(start_index, 0, len(self.data)))
        end = int(np.clip(end_index, 0, len(self.data)))
        if end <= start:
            return False

        arr = np.asarray(self.data, dtype=np.float32).flatten()
        remove_len = end - start
        self.data = np.concatenate([arr[:start], arr[end:]])

        updated_boundaries: list[int] = []
        for boundary in self.sample_boundaries:
            if boundary <= start:
                updated_boundaries.append(boundary)
            elif boundary <= end:
                continue
            else:
                updated_boundaries.append(boundary - remove_len)

        self.sample_boundaries = updated_boundaries
        self._normalize_boundaries()
        return True

    def insert_data(self, insert_index: int, data: np.ndarray, as_new_segment: bool = True) -> bool:
        incoming = np.asarray(data, dtype=np.float32).flatten()
        if incoming.size == 0:
            return False

        idx = int(np.clip(insert_index, 0, len(self.data)))
        arr = np.asarray(self.data, dtype=np.float32).flatten()
        self.data = np.concatenate([arr[:idx], incoming, arr[idx:]])

        shift = incoming.size
        shifted_boundaries: list[int] = []
        for boundary in self.sample_boundaries:
            if boundary >= idx:
                shifted_boundaries.append(boundary + shift)
            else:
                shifted_boundaries.append(boundary)

        self.sample_boundaries = shifted_boundaries
        if as_new_segment:
            if idx > 0 and idx not in self.sample_boundaries:
                self.sample_boundaries.append(idx)
            end_idx = idx + shift
            if end_idx not in self.sample_boundaries:
                self.sample_boundaries.append(end_idx)
        self._normalize_boundaries()
        return True

    def _normalize_boundaries(self) -> None:
        max_len = len(self.data)
        cleaned = sorted({int(b) for b in self.sample_boundaries if 0 < int(b) <= max_len})
        if max_len > 0 and (not cleaned or cleaned[-1] != max_len):
            cleaned.append(max_len)
        self.sample_boundaries = cleaned

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
