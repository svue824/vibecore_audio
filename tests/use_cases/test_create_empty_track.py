import pytest
import numpy as np
from audio_editor.use_cases.create_empty_track import CreateEmptyTrack
from audio_editor.domain.audio_track import AudioTrack


def test_create_empty_track_success():
    """
    Test that CreateEmptyTrack creates a valid AudioTrack
    with correct name, sample_rate, duration, and zero data.
    """
    # Arrange: define inputs
    name = "My Test Track"
    duration_seconds = 2.0  # seconds
    sample_rate = 44100  # Hz

    use_case = CreateEmptyTrack()

    # Act: execute the use case
    track = use_case.execute(name, duration_seconds, sample_rate)

    # Assert: track is correct type
    assert isinstance(track, AudioTrack), "Returned object must be an AudioTrack"

    # Assert: track name and sample_rate match input
    assert track.name == name
    assert track.sample_rate == sample_rate

    # Assert: track duration in samples is correct
    expected_samples = int(duration_seconds * sample_rate)
    assert len(track.data) == expected_samples, "Data length must equal duration * sample_rate"

    # Assert: all data samples are zeros
    assert np.all(track.data == 0), "All samples should be initialized to zero"


def test_create_empty_track_invalid_inputs():
    """
    Test that CreateEmptyTrack raises ValueError for invalid inputs
    """
    use_case = CreateEmptyTrack()

    # Negative duration
    with pytest.raises(ValueError):
        use_case.execute("Invalid Track", -1.0, 44100)

    # Zero sample rate
    with pytest.raises(ValueError):
        use_case.execute("Invalid Track", 1.0, 0)
