from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """Simple waveform preview widget for a mono or stereo numpy signal."""
    positionClicked = Signal(float)
    selectionChanged = Signal(float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._audio_data = np.array([], dtype=np.float32)
        self._playhead_position: float | None = None
        self._segment_markers: list[float] = []
        self._interaction_mode = "click"
        self._dragging_selection = False
        self._selection_start: float | None = None
        self._selection_end: float | None = None
        self.setMinimumHeight(160)

    def set_audio_data(self, data: np.ndarray | None) -> None:
        """Set waveform data and trigger repaint."""
        if data is None:
            self._audio_data = np.array([], dtype=np.float32)
        else:
            self._audio_data = self._normalize_to_mono(np.asarray(data, dtype=np.float32))
        self.update()

    def set_playhead_position(self, position: float | None) -> None:
        """Set playhead location as normalized [0,1], or None to hide it."""
        if position is None:
            self._playhead_position = None
        else:
            self._playhead_position = float(np.clip(position, 0.0, 1.0))
        self.update()

    def set_segment_markers(self, boundaries: list[int], total_samples: int) -> None:
        if total_samples <= 0:
            self._segment_markers = []
        else:
            self._segment_markers = [
                float(np.clip(boundary / total_samples, 0.0, 1.0))
                for boundary in boundaries
                if 0 < boundary < total_samples
            ]
        self.update()

    def set_interaction_mode(self, mode: str) -> None:
        """Set interaction mode: 'select' for drag selection, otherwise click."""
        self._interaction_mode = mode
        if mode != "select":
            self._dragging_selection = False

    def set_selection_range(self, start: float | None, end: float | None) -> None:
        if start is None or end is None:
            self._selection_start = None
            self._selection_end = None
        else:
            self._selection_start = float(np.clip(start, 0.0, 1.0))
            self._selection_end = float(np.clip(end, 0.0, 1.0))
        self.update()

    def clear_selection(self) -> None:
        self.set_selection_range(None, None)

    def _position_to_normalized(self, x: float) -> float:
        width = max(1, self.rect().width() - 1)
        return float(np.clip(x / width, 0.0, 1.0))

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

        if self._selection_start is not None and self._selection_end is not None:
            start = min(self._selection_start, self._selection_end)
            end = max(self._selection_start, self._selection_end)
            x1 = int(start * (width - 1))
            x2 = int(end * (width - 1))
            painter.fillRect(x1, 0, max(1, x2 - x1), height, QColor(110, 231, 255, 45))
            select_pen = QPen(QColor("#6EE7FF"))
            painter.setPen(select_pen)
            painter.drawLine(x1, 0, x1, height)
            painter.drawLine(x2, 0, x2, height)

        if self._segment_markers:
            segment_pen = QPen(QColor("#3A3A3A"))
            painter.setPen(segment_pen)
            for marker in self._segment_markers:
                x = int(marker * (width - 1))
                painter.drawLine(x, 0, x, height)

        if self._playhead_position is not None:
            playhead_x = int(self._playhead_position * (width - 1))
            playhead_pen = QPen(QColor("#FF8C42"))
            playhead_pen.setWidth(2)
            painter.setPen(playhead_pen)
            painter.drawLine(playhead_x, 0, playhead_x, height)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.button() != Qt.LeftButton:
            return
        position = self._position_to_normalized(event.position().x())
        if self._interaction_mode == "select":
            self._dragging_selection = True
            self._selection_start = position
            self._selection_end = position
            self.update()
            return
        self.positionClicked.emit(position)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if not self._dragging_selection or self._interaction_mode != "select":
            return
        self._selection_end = self._position_to_normalized(event.position().x())
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.button() != Qt.LeftButton:
            return
        if not self._dragging_selection or self._interaction_mode != "select":
            return
        self._dragging_selection = False
        self._selection_end = self._position_to_normalized(event.position().x())
        if self._selection_start is not None and self._selection_end is not None:
            start = min(self._selection_start, self._selection_end)
            end = max(self._selection_start, self._selection_end)
            self.selectionChanged.emit(start, end)
        self.update()
