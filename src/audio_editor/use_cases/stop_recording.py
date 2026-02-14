from audio_editor.services.audio_engine import AudioEngine
from audio_editor.domain.audio_track import AudioTrack


class StopRecording:
    def __init__(self, audio_engine: AudioEngine):
        self.audio_engine = audio_engine

    def execute(self, track: AudioTrack):
        audio = self.audio_engine.stop_recording()
        track.append_data(audio, as_new_segment=True)
