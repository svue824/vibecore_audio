from typing import List
from .audio_track import AudioTrack

class Project:
    """Represents a project containing multiple audio tracks."""

    def __init__(self, name: str):
        self.name = name
        self._tracks: List[AudioTrack] = []

    def add_track(self, track: AudioTrack) -> None:
        self._tracks.append(track)

    def remove_track(self, track: AudioTrack) -> None:
        self._tracks.remove(track)

    def insert_track_after(self, existing_track: AudioTrack, new_track: AudioTrack) -> None:
        index = self._tracks.index(existing_track)
        self._tracks.insert(index + 1, new_track)

    def get_tracks(self) -> List[AudioTrack]:
        return list(self._tracks)

    def track_count(self) -> int:
        return len(self._tracks)
