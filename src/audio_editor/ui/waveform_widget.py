from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """Simple waveform preview widget for a mono or stereo numpy signal."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._audio_data = np.array([], dtype=np.float32)
        self.setMinimumHeight(160)

    def set_audio_data(self, data: np.ndarray | None) -> None:
        """Set waveform data and trigger repaint."""
        if data is None:
            self._audio_data = np.array([], dtype=np.float32)
        else:
            self._audio_data = self._normalize_to_mono(np.asarray(data, dtype=np.float32))
        self.update()

    @staticmethod
    def _normalize_to_mono(data: np.ndarray) -> np.ndarray:
        if data.ndim == 1:
            return data
        if data.ndim == 2:
            return data.mean(axis=1)
        return data.flatten()

    @staticmethod
    def build_peaks(data: np.ndarray, bins: int) -> np.ndarray:
        """Compress full signal into peak magnitudes for each horizontal bin."""
        if bins <= 0:
            return np.array([], dtype=np.float32)
        if data.size == 0:
            return np.zeros(bins, dtype=np.float32)

        clipped = np.clip(data.astype(np.float32), -1.0, 1.0)
        chunk_size = max(1, int(np.ceil(len(clipped) / bins)))

        peaks: list[float] = []
        for start in range(0, len(clipped), chunk_size):
            chunk = clipped[start : start + chunk_size]
            peaks.append(float(np.max(np.abs(chunk))))

        if len(peaks) < bins:
            peaks.extend([0.0] * (bins - len(peaks)))

        return np.asarray(peaks[:bins], dtype=np.float32)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        rect = self.rect()
        painter.fillRect(rect, QColor("#121212"))

        width = max(1, rect.width())
        height = rect.height()
        mid_y = height / 2

        axis_pen = QPen(QColor("#2F2F2F"))
        painter.setPen(axis_pen)
        painter.drawLine(0, int(mid_y), width, int(mid_y))

        if self._audio_data.size == 0:
            return

        peaks = self.build_peaks(self._audio_data, width)
        wave_pen = QPen(QColor("#6EE7FF"))
        painter.setPen(wave_pen)

        max_amplitude = (height / 2) - 6
        for x, value in enumerate(peaks):
            half_line = max_amplitude * float(value)
            painter.drawLine(x, int(mid_y - half_line), x, int(mid_y + half_line))
