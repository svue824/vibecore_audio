from audio_editor.domain.project import Project
from audio_editor.domain.audio_track import AudioTrack

class DeleteTrackFromProject:
    """Use case for deleting a track from a project."""

    def __init__(self, project: Project):
        self.project = project
    
    def execute(self, track: AudioTrack):
        if track not in self.project.get_tracks():
            raise ValueError(f"Track {track.name} not found in project.")
        self.project.get_tracks().remove(track)