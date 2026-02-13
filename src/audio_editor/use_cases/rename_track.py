from audio_editor.domain.project import Project
from audio_editor.domain.audio_track import AudioTrack

class RenameTrack:
    """Use case for renaming a track within a project."""

    def __init__(self, project: Project):
        self.project = project
    
    def execute(self, track: AudioTrack, new_name: str):
        if not new_name.strip():
            raise ValueError("Track name cannot be empty")
        if any(t.name == new_name for t in self.project.get_tracks()):
            raise ValueError(f"A track with name '{new_name}' already exists")
        track.rename(new_name)
