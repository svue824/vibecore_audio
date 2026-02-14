from audio_editor.services.audio_engine import AudioEngine


class StartRecording:
    def __init__(self, audio_engine: AudioEngine):
        self.audio_engine = audio_engine

    def execute(self, sample_rate: int):
        self.audio_engine.start_recording(sample_rate)
