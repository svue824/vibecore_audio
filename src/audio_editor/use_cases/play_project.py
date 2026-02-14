from typing import List
from audio_editor.services.audio_engine import AudioEngine
from audio_editor.domain.audio_track import AudioTrack


class PlayProject:
    def __init__(self, audio_engine: AudioEngine):
        self.audio_engine = audio_engine

    def execute(self, tracks: List[AudioTrack]):
        self.audio_engine.play_project(tracks)
