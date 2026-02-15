from __future__ import annotations

import json
import numpy as np
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QColor, QPainter, QPen, QDrag
from PySide6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """Simple waveform preview widget for a mono or stereo numpy signal."""
    positionClicked = Signal(float)
    selectionChanged = Signal(float, float)
    selectionDropped = Signal(str, float, float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._audio_data = np.array([], dtype=np.float32)
        self._playhead_position: float | None = None
        self._segment_markers: list[float] = []
        self._track_key = ""
        self._interaction_mode = "click"
        self._dragging_selection = False
        self._drag_candidate = False
        self._drag_start_x = 0.0
        self._selection_start: float | None = None
        self._selection_end: float | None = None
        self.setAcceptDrops(True)
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
        """Set interaction mode: 'select', 'segment_drag', or 'click'."""
        self._interaction_mode = mode
        if mode != "select":
            self._dragging_selection = False
            self._drag_candidate = False

    def set_track_key(self, track_key: str) -> None:
        self._track_key = track_key

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

        border_pen = QPen(QColor("#2A2A2A"))
        painter.setPen(border_pen)
        painter.drawLine(0, 0, width - 1, 0)
        painter.drawLine(0, height - 1, width - 1, height - 1)

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
            if self._selection_start is not None and self._selection_end is not None:
                start = min(self._selection_start, self._selection_end)
                end = max(self._selection_start, self._selection_end)
                if start <= position <= end:
                    self._drag_candidate = True
                    self._drag_start_x = event.position().x()
                    return
            self._dragging_selection = True
            self._selection_start = position
            self._selection_end = position
            self.update()
            return
        if self._interaction_mode == "segment_drag":
            if self._selection_start is not None and self._selection_end is not None:
                start = min(self._selection_start, self._selection_end)
                end = max(self._selection_start, self._selection_end)
                if start <= position <= end:
                    self._drag_candidate = True
                    self._drag_start_x = event.position().x()
                    return
            self.positionClicked.emit(position)
            return
        self.positionClicked.emit(position)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if self._drag_candidate and self._interaction_mode in ("select", "segment_drag"):
            if abs(event.position().x() - self._drag_start_x) >= 6:
                self._drag_candidate = False
                self._start_selection_drag()
            return
        if not self._dragging_selection or self._interaction_mode != "select":
            return
        self._selection_end = self._position_to_normalized(event.position().x())
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.button() != Qt.LeftButton:
            return
        if self._drag_candidate:
            self._drag_candidate = False
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

    def _start_selection_drag(self) -> None:
        if self._selection_start is None or self._selection_end is None or not self._track_key:
            return
        start = min(self._selection_start, self._selection_end)
        end = max(self._selection_start, self._selection_end)
        if end <= start:
            return

        payload = {
            "source_track_key": self._track_key,
            "selection_start": start,
            "selection_end": end,
        }
        mime_data = QMimeData()
        mime_data.setData(
            "application/x-vibecore-selection",
            json.dumps(payload).encode("utf-8"),
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.mimeData().hasFormat("application/x-vibecore-selection"):
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.mimeData().hasFormat("application/x-vibecore-selection"):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if not event.mimeData().hasFormat("application/x-vibecore-selection"):
            event.ignore()
            return
        try:
            payload_bytes = event.mimeData().data("application/x-vibecore-selection").data()
            payload = json.loads(payload_bytes.decode("utf-8"))
            source_track_key = str(payload["source_track_key"])
            selection_start = float(payload["selection_start"])
            selection_end = float(payload["selection_end"])
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            event.ignore()
            return

        drop_position = self._position_to_normalized(event.position().x())
        self.selectionDropped.emit(source_track_key, selection_start, selection_end, drop_position)
        event.acceptProposedAction()


class TimelineWidget(QWidget):
    """Project-level timeline ruler with a single playhead."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._duration_seconds = 0.0
        self._playhead_position: float | None = None
        self.setMinimumHeight(36)
        self.setMaximumHeight(36)

    def set_duration_seconds(self, duration_seconds: float) -> None:
        self._duration_seconds = max(0.0, float(duration_seconds))
        self.update()

    def set_playhead_position(self, position: float | None) -> None:
        if position is None:
            self._playhead_position = None
        else:
            self._playhead_position = float(np.clip(position, 0.0, 1.0))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        rect = self.rect()
        painter.fillRect(rect, QColor("#111111"))

        if rect.width() <= 1:
            return

        left = 0
        right = rect.width() - 1
        baseline_y = rect.height() - 12

        axis_pen = QPen(QColor("#3A3A3A"))
        painter.setPen(axis_pen)
        painter.drawLine(left, baseline_y, right, baseline_y)

        label_pen = QPen(QColor("#9D9D9D"))
        painter.setPen(label_pen)

        duration = max(self._duration_seconds, 0.0)
        if duration <= 0.0:
            painter.drawText(2, 11, "0.0s")
        else:
            target_ticks = 6
            raw_step = duration / target_ticks
            if raw_step <= 0.25:
                step = 0.25
            elif raw_step <= 0.5:
                step = 0.5
            elif raw_step <= 1.0:
                step = 1.0
            elif raw_step <= 2.0:
                step = 2.0
            elif raw_step <= 5.0:
                step = 5.0
            else:
                step = 10.0

            tick_time = 0.0
            while tick_time <= duration + 1e-6:
                ratio = tick_time / duration if duration > 0 else 0.0
                x = int(left + ratio * (right - left))
                painter.drawLine(x, baseline_y - 5, x, baseline_y + 2)
                painter.drawText(x + 2, 11, f"{tick_time:.1f}s")
                tick_time += step

            if duration % step > 1e-6:
                painter.drawLine(right, baseline_y - 5, right, baseline_y + 2)
                painter.drawText(max(2, right - 40), 11, f"{duration:.1f}s")

        if self._playhead_position is not None:
            playhead_x = int(left + self._playhead_position * (right - left))
            playhead_pen = QPen(QColor("#FF8C42"))
            playhead_pen.setWidth(2)
            painter.setPen(playhead_pen)
            painter.drawLine(playhead_x, 0, playhead_x, rect.height())
