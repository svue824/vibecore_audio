import numpy as np

from audio_editor.ui.waveform_widget import WaveformWidget


def test_build_peaks_for_empty_data_returns_zeros():
    peaks = WaveformWidget.build_peaks(np.array([], dtype=np.float32), bins=5)

    assert np.array_equal(peaks, np.zeros(5, dtype=np.float32))


def test_build_peaks_compresses_signal_to_requested_bins():
    data = np.array([-1.0, -0.5, 0.25, 0.75], dtype=np.float32)

    peaks = WaveformWidget.build_peaks(data, bins=2)

    assert np.allclose(peaks, np.array([1.0, 0.75], dtype=np.float32))


def test_normalize_to_mono_from_stereo():
    stereo = np.array([[1.0, -1.0], [0.5, 0.25]], dtype=np.float32)

    mono = WaveformWidget._normalize_to_mono(stereo)

    assert np.allclose(mono, np.array([0.0, 0.375], dtype=np.float32))


def test_set_playhead_position_clamps_values():
    widget = WaveformWidget()

    widget.set_playhead_position(1.7)
    assert widget._playhead_position == 1.0

    widget.set_playhead_position(-0.2)
    assert widget._playhead_position == 0.0

    widget.set_playhead_position(None)
    assert widget._playhead_position is None
