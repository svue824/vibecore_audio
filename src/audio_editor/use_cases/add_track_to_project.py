from audio_editor.domain.project import Project
from audio_editor.domain.audio_track import AudioTrack

class AddTrackToProject:
    """Use case for adding a track to a project."""

    def __init__(self, project: Project):
        self.project = project

    def execute(self, track: AudioTrack):
        # Example business rule: no duplicate names
        if any(t.name == track.name for t in self.project.get_tracks()):
            raise ValueError(f"Track with name {track.name} already exists")
        self.project.add_track(track)
