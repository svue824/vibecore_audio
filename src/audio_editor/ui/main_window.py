import json
import os
import sys
import time
import wave
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QInputDialog,
    QSlider,
    QCheckBox,
    QScrollArea,
    QComboBox,
    QToolButton,
    QMenu,
    QFileDialog,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Slot, QSize, QTimer
from PySide6.QtGui import QShortcut, QKeySequence, QAction

from audio_editor.domain.audio_track import AudioTrack
from audio_editor.domain.project import Project
from audio_editor.use_cases.add_track_to_project import AddTrackToProject
from audio_editor.use_cases.delete_track_from_project import DeleteTrackFromProject
from audio_editor.ui.styles import DARK_STYLE
from audio_editor.use_cases.rename_track import RenameTrack
from audio_editor.services.audio_engine import AudioEngine
from audio_editor.use_cases.start_recording import StartRecording
from audio_editor.use_cases.stop_recording import StopRecording
import numpy as np
from audio_editor.ui.waveform_widget import WaveformWidget


class MainWindow(QMainWindow):
    TOOL_NONE = "None"
    TOOL_SELECT = "Select Tool"
    TOOL_SPLIT = "Split Tool"
    TOOL_SPLIT_SAMPLE = "Split Sample Tool"
    TOOL_CUT_BACKWARD = "Backward Cut Tool"
    TOOL_CUT_FORWARD = "Forward Cut Tool"

    def __init__(self):
        super().__init__()
        self.audio_engine = AudioEngine()
        self.track_waveform_widgets: dict[int, WaveformWidget] = {}
        self.track_waveform_labels: dict[int, QLabel] = {}
        self.transport_timer = QTimer(self)
        self.transport_timer.setInterval(33)
        self.transport_timer.timeout.connect(self.update_transport_visuals)
        self.transport_mode: str | None = None
        self.transport_start_time = 0.0
        self.transport_duration_seconds = 0.0
        self.transport_track_ids: set[int] = set()
        self.transport_record_track_id: int | None = None
        self.transport_record_sample_rate = 44100
        self.record_visual_window_seconds = 15.0
        self.current_edit_tool = self.TOOL_NONE
        self.track_selection_ranges: dict[int, tuple[float, float]] = {}
        self.clipboard_audio = np.array([], dtype=np.float32)
        self.clipboard_sample_rate = 44100
        self.project_file_path: str | None = None
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []
        self.max_history = 100
        self._restoring_history = False

        self.setWindowTitle("VibeCore Audio")
        self.setMinimumSize(1120, 680)
        self.resize(1440, 780)
        self.setStyleSheet(DARK_STYLE)

        # ===== Domain State =====
        self.project = Project("My Project")

        # ===== Central Widget =====
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)
        central_widget.setLayout(root_layout)

        # ===== Top Action Bar =====
        action_bar_widget = QWidget()
        action_bar_widget.setObjectName("actionBarHost")
        action_bar_layout = QHBoxLayout()
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
        action_bar_layout.setSpacing(0)
        action_bar_widget.setLayout(action_bar_layout)
        root_layout.addWidget(action_bar_widget)

        self.action_strip = QWidget()
        self.action_strip.setObjectName("actionStrip")
        self.action_strip.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        action_strip_layout = QHBoxLayout()
        action_strip_layout.setContentsMargins(12, 10, 12, 10)
        action_strip_layout.setSpacing(6)
        self.action_strip.setLayout(action_strip_layout)
        action_bar_layout.addWidget(self.action_strip, 1)

        def add_action_divider():
            divider = QFrame()
            divider.setFrameShape(QFrame.VLine)
            divider.setFrameShadow(QFrame.Plain)
            divider.setObjectName("actionDivider")
            action_strip_layout.addWidget(divider)

        self.file_button = QToolButton()
        self.file_button.setObjectName("fileButton")
        self.file_button.setText("File")
        self.file_button.setPopupMode(QToolButton.InstantPopup)
        self.file_button.setMinimumWidth(84)
        self.file_menu = QMenu(self.file_button)
        self.file_button.setMenu(self.file_menu)
        action_strip_layout.addWidget(self.file_button)

        self.file_insert_action = QAction("Insert File...", self)
        self.file_insert_action.triggered.connect(self.handle_insert_file)
        self.file_menu.addAction(self.file_insert_action)

        self.file_open_project_action = QAction("Open Project...", self)
        self.file_open_project_action.triggered.connect(self.handle_open_project)
        self.file_menu.addAction(self.file_open_project_action)

        self.file_save_action = QAction("Save Project", self)
        self.file_save_action.triggered.connect(self.handle_save_project)
        self.file_menu.addAction(self.file_save_action)

        self.file_save_as_action = QAction("Save Project As...", self)
        self.file_save_as_action.triggered.connect(self.handle_save_project_as)
        self.file_menu.addAction(self.file_save_as_action)

        self.file_menu.addSeparator()
        self.file_export_action = QAction("Export Mix...", self)
        self.file_export_action.triggered.connect(self.handle_export_mix)
        self.file_menu.addAction(self.file_export_action)

        self.add_button = QPushButton("Add Track")
        self.add_button.setObjectName("actionButton")
        self.add_button.clicked.connect(self.handle_add_track)
        action_strip_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("Delete Track")
        self.delete_button.setObjectName("actionButton")
        self.delete_button.clicked.connect(self.handle_delete_track)
        self.delete_button.setEnabled(False)
        self.delete_button.setObjectName("deleteButton")
        action_strip_layout.addWidget(self.delete_button)

        self.rename_button = QPushButton("Rename Track")
        self.rename_button.setObjectName("actionButton")
        self.rename_button.clicked.connect(self.handle_rename_track)
        action_strip_layout.addWidget(self.rename_button)
        add_action_divider()

        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("transportButton")
        self.play_button.setToolTip("Play")
        self.play_button.clicked.connect(self.handle_play)
        action_strip_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("■")
        self.stop_button.setObjectName("transportButton")
        self.stop_button.setToolTip("Stop")
        self.stop_button.clicked.connect(self.handle_stop)
        action_strip_layout.addWidget(self.stop_button)

        self.record_button = QPushButton("●")
        self.record_button.setObjectName("recordButton")
        self.record_button.setToolTip("Record")
        self.record_button.clicked.connect(self.handle_record_toggle)
        action_strip_layout.addWidget(self.record_button)
        add_action_divider()

        self.cut_button = QPushButton("Cut")
        self.cut_button.setObjectName("actionButton")
        self.cut_button.clicked.connect(self.handle_cut_selection)
        self.cut_button.setEnabled(False)
        action_strip_layout.addWidget(self.cut_button)

        self.undo_button = QPushButton("Undo")
        self.undo_button.setObjectName("actionButton")
        self.undo_button.clicked.connect(self.handle_undo)
        self.undo_button.setEnabled(False)
        action_strip_layout.addWidget(self.undo_button)

        self.redo_button = QPushButton("Redo")
        self.redo_button.setObjectName("actionButton")
        self.redo_button.clicked.connect(self.handle_redo)
        self.redo_button.setEnabled(False)
        action_strip_layout.addWidget(self.redo_button)

        self.copy_button = QPushButton("Copy")
        self.copy_button.setObjectName("actionButton")
        self.copy_button.clicked.connect(self.handle_copy_selection)
        self.copy_button.setEnabled(False)
        action_strip_layout.addWidget(self.copy_button)

        self.paste_button = QPushButton("Paste")
        self.paste_button.setObjectName("actionButton")
        self.paste_button.clicked.connect(self.handle_paste_selection)
        self.paste_button.setEnabled(False)
        action_strip_layout.addWidget(self.paste_button)
        add_action_divider()

        self.play_project_button = QPushButton("Play Project")
        self.play_project_button.setObjectName("actionButton")
        self.play_project_button.clicked.connect(self.handle_play_project)
        action_strip_layout.addWidget(self.play_project_button)
        add_action_divider()

        tools_label = QLabel("Tool")
        tools_label.setObjectName("actionLabel")
        action_strip_layout.addWidget(tools_label)

        self.tools_dropdown = QComboBox()
        self.tools_dropdown.setObjectName("toolPicker")
        self.tools_dropdown.setMinimumWidth(136)
        self.tools_dropdown.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        self.tools_dropdown.addItems(
            [
                self.TOOL_NONE,
                self.TOOL_SELECT,
                self.TOOL_SPLIT,
                self.TOOL_SPLIT_SAMPLE,
                self.TOOL_CUT_BACKWARD,
                self.TOOL_CUT_FORWARD,
            ]
        )
        self.tools_dropdown.currentTextChanged.connect(self.on_tool_changed)
        action_strip_layout.addWidget(self.tools_dropdown)
        action_strip_layout.addStretch(1)

        # ===== Main Panels (Left + Right) =====
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        root_layout.addLayout(main_layout)

        # ===== Left Sidebar =====
        self.track_list = QListWidget()
        self.track_list.setFixedWidth(220)
        self.track_list.setSpacing(4)

        # ----- NEW: Enable drag-and-drop reordering -----
        self.track_list.setDragDropMode(QListWidget.InternalMove)
        self.track_list.setDefaultDropAction(Qt.MoveAction)
        self.track_list.model().rowsMoved.connect(self.handle_reorder_tracks)

        self.track_list.itemSelectionChanged.connect(self.on_track_selected)
        main_layout.addWidget(self.track_list)

        # ===== Right Content Area =====
        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
        right_layout.setSpacing(12)
        right_container.setLayout(right_layout)
        main_layout.addWidget(right_container)

        # Title
        self.title_label = QLabel("VibeCore Audio")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.title_label)

        # Subtitle / Track count
        self.sub_label = QLabel("Create and manage audio tracks")
        self.sub_label.setObjectName("subLabel")
        self.sub_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.sub_label)

        self.waveforms_scroll = QScrollArea()
        self.waveforms_scroll.setWidgetResizable(True)
        self.waveforms_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.waveforms_container = QWidget()
        self.waveforms_layout = QVBoxLayout()
        self.waveforms_layout.setAlignment(Qt.AlignTop)
        self.waveforms_layout.setSpacing(10)
        self.waveforms_container.setLayout(self.waveforms_layout)

        self.waveforms_scroll.setWidget(self.waveforms_container)
        right_layout.addWidget(self.waveforms_scroll)

        self.delete_selection_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.delete_selection_shortcut.activated.connect(self.handle_delete_key)
        self.backspace_selection_shortcut = QShortcut(QKeySequence(Qt.Key_Backspace), self)
        self.backspace_selection_shortcut.activated.connect(self.handle_delete_key)
        self.copy_selection_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.copy_selection_shortcut.activated.connect(self.handle_copy_selection)
        self.paste_selection_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        self.paste_selection_shortcut.activated.connect(self.handle_paste_selection)
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.handle_undo)
        self.redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.redo_shortcut.activated.connect(self.handle_redo)
        self.redo_shortcut_alt = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self.redo_shortcut_alt.activated.connect(self.handle_redo)

    @Slot()
    def handle_reorder_tracks(self):
        """Sync project tracks with the current sidebar order."""
        self.push_undo_state()
        new_order = []
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            # Get the widget to extract track name
            widget = self.track_list.itemWidget(item)
            if widget:
                # Extract track name from the label in the widget
                label = widget.layout().itemAt(0).widget()
                track_name = label.text()
            else:
                # Fallback for text items
                item_text = item.text()
                track_name = item_text.split(" (")[0]
            
            track = next((t for t in self.project.get_tracks() if t.name == track_name), None)
            if track:
                new_order.append(track)
        self.project._tracks = new_order
        self.refresh_waveform_panel()

    # ----- Handlers -----
    def handle_add_track(self):
        self.push_undo_state()
        track_number = self.project.track_count() + 1
        new_track = AudioTrack(
            name=f"Track {track_number}",
            sample_rate=44100,
            data=np.array([], dtype=np.float32)
        )

        # Use AddTrackToProject use case
        add_use_case = AddTrackToProject(self.project)
        add_use_case.execute(new_track)

        # Mute box & vol slider
        self.add_track_ui_item(new_track)
        self.add_waveform_ui_item(new_track)

        # Update subtitle
        self.sub_label.setText(f"{self.project.track_count()} track(s) in project")

    # When adding a track, create a container widget
    def add_track_ui_item(self, track):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Track label
        label = QLabel(track.name)
        layout.addWidget(label)

        # Volume slider
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(int(track.volume * 100))
        slider.valueChanged.connect(lambda val, t=track: self.on_volume_changed(t, val))
        layout.addWidget(slider)

        # Mute checkbox
        mute_checkbox = QCheckBox("Mute")
        mute_checkbox.setChecked(track.muted)
        mute_checkbox.toggled.connect(lambda checked, t=track: self.on_mute_toggled(t, checked))
        layout.addWidget(mute_checkbox)

        container.setLayout(layout)

        # Insert into QListWidget
        item = QListWidgetItem()
        self.track_list.addItem(item)
        self.track_list.setItemWidget(item, container)
        row_height = max(container.sizeHint().height() + 10, 42)
        item.setSizeHint(QSize(0, row_height))

    def add_waveform_ui_item(self, track: AudioTrack):
        row = QWidget()
        row_layout = QVBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        label = QLabel(track.name)
        label.setObjectName("subLabel")
        row_layout.addWidget(label)

        waveform = WaveformWidget()
        waveform.setFixedHeight(90)
        waveform.set_track_key(self._track_key(track))
        self._apply_track_visual_state(track, waveform)
        waveform.positionClicked.connect(lambda pos, t=track: self.on_waveform_clicked(t, pos))
        waveform.selectionChanged.connect(
            lambda start, end, t=track: self.on_waveform_selection_changed(t, start, end)
        )
        waveform.selectionDropped.connect(
            lambda source_key, start, end, drop_pos, t=track: self.on_selection_dropped(
                t, source_key, start, end, drop_pos
            )
        )
        waveform.set_interaction_mode(self._waveform_interaction_mode_for_tool())
        selected_range = self.track_selection_ranges.get(id(track))
        if selected_range:
            waveform.set_selection_range(selected_range[0], selected_range[1])
        else:
            waveform.clear_selection()
        row_layout.addWidget(waveform)

        row.setLayout(row_layout)
        self.waveforms_layout.addWidget(row)
        self.track_waveform_widgets[id(track)] = waveform
        self.track_waveform_labels[id(track)] = label

    def refresh_waveform_panel(self):
        while self.waveforms_layout.count():
            item = self.waveforms_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.track_waveform_widgets.clear()
        self.track_waveform_labels.clear()

        for track in self.project.get_tracks():
            self.add_waveform_ui_item(track)

    def sync_waveform_for_track(self, track: AudioTrack):
        waveform = self.track_waveform_widgets.get(id(track))
        if waveform:
            self._apply_track_visual_state(track, waveform)
            selected_range = self.track_selection_ranges.get(id(track))
            if selected_range:
                waveform.set_selection_range(selected_range[0], selected_range[1])
            else:
                waveform.clear_selection()
        label = self.track_waveform_labels.get(id(track))
        if label:
            label.setText(track.name)

    def refresh_track_list(self, selected_track_id: int | None = None):
        self.track_list.blockSignals(True)
        self.track_list.clear()
        selected_row = -1
        for idx, track in enumerate(self.project.get_tracks()):
            self.add_track_ui_item(track)
            if selected_track_id is not None and id(track) == selected_track_id:
                selected_row = idx
        self.track_list.blockSignals(False)
        if selected_row >= 0:
            self.track_list.setCurrentRow(selected_row)
        self.delete_button.setEnabled(self.track_list.currentRow() != -1)

    def clear_all_playheads(self):
        for waveform in self.track_waveform_widgets.values():
            waveform.set_playhead_position(None)

    def start_transport(
        self,
        mode: str,
        track_ids: set[int],
        duration_seconds: float,
        record_track_id: int | None = None,
        record_sample_rate: int = 44100,
    ):
        self.clear_all_playheads()
        self.transport_mode = mode
        self.transport_track_ids = track_ids
        self.transport_duration_seconds = duration_seconds
        self.transport_record_track_id = record_track_id
        self.transport_record_sample_rate = record_sample_rate
        self.transport_start_time = time.perf_counter()
        self.transport_timer.start()
        self.update_transport_visuals()

    def stop_transport(self):
        self.transport_timer.stop()
        self.transport_mode = None
        self.transport_track_ids.clear()
        self.transport_duration_seconds = 0.0
        self.transport_record_track_id = None
        self.transport_record_sample_rate = 44100
        self.clear_all_playheads()

    @Slot()
    def update_transport_visuals(self):
        if self.transport_mode is None:
            return

        elapsed = time.perf_counter() - self.transport_start_time

        if self.transport_mode == "record":
            if not self.audio_engine.is_recording() or self.transport_record_track_id is None:
                self.stop_transport()
                return

            waveform = self.track_waveform_widgets.get(self.transport_record_track_id)
            if waveform is None:
                return

            preview = self.audio_engine.get_recording_preview()
            window_samples = max(
                1,
                int(self.transport_record_sample_rate * self.record_visual_window_seconds),
            )
            if preview.size <= window_samples:
                padded_preview = np.pad(preview, (0, window_samples - preview.size))
                waveform.set_audio_data(padded_preview)
                playhead = preview.size / window_samples
            else:
                waveform.set_audio_data(preview[-window_samples:])
                playhead = 1.0
            waveform.set_playhead_position(playhead)
            return

        if self.transport_duration_seconds <= 0:
            self.stop_transport()
            return

        progress = min(1.0, elapsed / self.transport_duration_seconds)

        if self.transport_mode == "play_track":
            for track_id in self.transport_track_ids:
                waveform = self.track_waveform_widgets.get(track_id)
                if waveform is not None:
                    waveform.set_playhead_position(progress)
        elif self.transport_mode == "play_project":
            for track in self.project.get_tracks():
                waveform = self.track_waveform_widgets.get(id(track))
                if waveform is None or len(track.data) == 0:
                    continue
                track_duration = len(track.data) / max(track.sample_rate, 1)
                if track_duration <= 0:
                    waveform.set_playhead_position(0.0)
                else:
                    waveform.set_playhead_position(min(1.0, elapsed / track_duration))

        if progress >= 1.0:
            self.stop_transport()

    def on_track_selected(self):
        selected = self.track_list.currentRow()
        self.delete_button.setEnabled(selected != -1)

    def on_tool_changed(self, tool_name: str):
        self.current_edit_tool = tool_name
        if tool_name != self.TOOL_SELECT:
            self.track_selection_ranges.clear()
        for track in self.project.get_tracks():
            waveform = self.track_waveform_widgets.get(id(track))
            if waveform:
                waveform.set_interaction_mode(self._waveform_interaction_mode_for_tool())
                if tool_name != self.TOOL_SELECT:
                    waveform.clear_selection()
        self.update_cut_controls()

    def _waveform_interaction_mode_for_tool(self) -> str:
        if self.current_edit_tool == self.TOOL_SELECT:
            return "select"
        if self.current_edit_tool == self.TOOL_NONE:
            return "segment_drag"
        return "click"

    def _track_data_array(self, track: AudioTrack) -> np.ndarray:
        return np.asarray(track.data, dtype=np.float32).flatten()

    def _track_key(self, track: AudioTrack) -> str:
        return str(id(track))

    def _find_track_by_key(self, track_key: str) -> AudioTrack | None:
        return next((track for track in self.project.get_tracks() if self._track_key(track) == track_key), None)

    def _apply_track_visual_state(self, track: AudioTrack, waveform: WaveformWidget):
        data = self._track_data_array(track)
        waveform.set_audio_data(data)
        waveform.set_segment_markers(track.sample_boundaries, len(data))

    def _sample_index_from_normalized(self, track: AudioTrack, position: float) -> int:
        data = self._track_data_array(track)
        if data.size == 0:
            return 0
        return int(np.clip(position, 0.0, 1.0) * data.size)

    def _generate_unique_track_name(self, base_name: str) -> str:
        existing = {t.name for t in self.project.get_tracks()}
        if base_name not in existing:
            return base_name
        counter = 2
        while True:
            candidate = f"{base_name} {counter}"
            if candidate not in existing:
                return candidate
            counter += 1

    def on_waveform_selection_changed(self, track: AudioTrack, start: float, end: float):
        if self.current_edit_tool != self.TOOL_SELECT:
            return
        self.track_selection_ranges[id(track)] = (start, end)
        self.sub_label.setText(
            f"Selected {int(start * 100)}% - {int(end * 100)}% on {track.name}"
        )
        self.update_cut_controls()

    def on_selection_dropped(
        self,
        target_track: AudioTrack,
        source_track_key: str,
        selection_start: float,
        selection_end: float,
        drop_position: float,
    ):
        if self.current_edit_tool not in (self.TOOL_SELECT, self.TOOL_NONE):
            return

        source_track = self._find_track_by_key(source_track_key)
        if source_track is None:
            return

        source_data = self._track_data_array(source_track)
        if source_data.size == 0:
            return

        src_start = int(np.clip(min(selection_start, selection_end), 0.0, 1.0) * source_data.size)
        src_end = int(np.clip(max(selection_start, selection_end), 0.0, 1.0) * source_data.size)
        if src_end <= src_start:
            return

        moved_segment = source_data[src_start:src_end].copy()
        if moved_segment.size == 0:
            return

        self.push_undo_state()
        target_data_before = self._track_data_array(target_track)
        target_drop_index = int(np.clip(drop_position, 0.0, 1.0) * target_data_before.size)

        if source_track is target_track:
            source_track.cut_range(src_start, src_end)
            moved_len = src_end - src_start
            if target_drop_index > src_end:
                target_drop_index -= moved_len
            elif src_start < target_drop_index <= src_end:
                target_drop_index = src_start
            snapped_index = source_track.nearest_boundary(target_drop_index)
            source_track.insert_data(snapped_index, moved_segment, as_new_segment=True)
            self.track_selection_ranges.pop(id(source_track), None)
            self.stop_transport()
            self.sync_waveform_for_track(source_track)
            self.update_cut_controls()
            self.sub_label.setText(f"Moved selection within {source_track.name}")
            return

        source_track.cut_range(src_start, src_end)
        snapped_index = target_track.nearest_boundary(target_drop_index)
        target_track.insert_data(snapped_index, moved_segment, as_new_segment=True)

        self.track_selection_ranges.pop(id(source_track), None)
        self.stop_transport()
        self.sync_waveform_for_track(source_track)
        self.sync_waveform_for_track(target_track)
        self.update_cut_controls()
        self.sub_label.setText(f"Moved selection from {source_track.name} to {target_track.name}")

    def on_waveform_clicked(self, track: AudioTrack, position: float):
        if self.current_edit_tool == self.TOOL_NONE:
            self.select_entire_clip_at(track, position)
        elif self.current_edit_tool == self.TOOL_SPLIT:
            self.split_track_at(track, position)
        elif self.current_edit_tool == self.TOOL_SPLIT_SAMPLE:
            self.split_sample_at(track, position)
        elif self.current_edit_tool == self.TOOL_CUT_BACKWARD:
            self.cut_track_backward(track, position)
        elif self.current_edit_tool == self.TOOL_CUT_FORWARD:
            self.cut_track_forward(track, position)

    def select_entire_clip_at(self, track: AudioTrack, position: float):
        data = self._track_data_array(track)
        if data.size == 0:
            return

        idx = self._sample_index_from_normalized(track, position)
        idx = int(np.clip(idx, 0, data.size - 1))

        clip_start = 0
        clip_end = data.size
        for boundary in track.sample_boundaries:
            if idx < boundary:
                clip_end = boundary
                break
            clip_start = boundary

        if clip_end <= clip_start:
            return

        self.track_selection_ranges.clear()
        self.track_selection_ranges[id(track)] = (
            clip_start / data.size,
            clip_end / data.size,
        )
        for existing_track in self.project.get_tracks():
            self.sync_waveform_for_track(existing_track)
        self.update_cut_controls()
        self.sub_label.setText(f"Selected clip in {track.name}")

    def update_cut_controls(self):
        has_selection = bool(self.track_selection_ranges)
        can_cut = self.current_edit_tool in (self.TOOL_SELECT, self.TOOL_NONE) and has_selection
        self.cut_button.setEnabled(can_cut)
        self.copy_button.setEnabled(has_selection)
        self.paste_button.setEnabled(self.clipboard_audio.size > 0)
        self.undo_button.setEnabled(len(self.undo_stack) > 0)
        self.redo_button.setEnabled(len(self.redo_stack) > 0)

    def capture_editor_state(self) -> dict:
        selected_row = self.track_list.currentRow()
        tracks_state = []
        track_index_by_id: dict[int, int] = {}
        tracks = self.project.get_tracks()
        for idx, track in enumerate(tracks):
            track_index_by_id[id(track)] = idx
            tracks_state.append(
                {
                    "name": track.name,
                    "sample_rate": track.sample_rate,
                    "data": self._track_data_array(track).copy(),
                    "file_path": track.file_path,
                    "volume": track.volume,
                    "muted": track.muted,
                    "sample_boundaries": list(track.sample_boundaries),
                }
            )

        selections_by_index: dict[int, tuple[float, float]] = {}
        for track_id, selection in self.track_selection_ranges.items():
            idx = track_index_by_id.get(track_id)
            if idx is not None:
                selections_by_index[idx] = selection

        return {
            "tracks": tracks_state,
            "selected_row": selected_row,
            "selections_by_index": selections_by_index,
        }

    def restore_editor_state(self, state: dict) -> None:
        self._restoring_history = True
        try:
            restored_tracks: list[AudioTrack] = []
            for item in state.get("tracks", []):
                track = AudioTrack(
                    name=item["name"],
                    sample_rate=item["sample_rate"],
                    data=np.asarray(item["data"], dtype=np.float32),
                    file_path=item.get("file_path"),
                    volume=item.get("volume", 1.0),
                    muted=item.get("muted", False),
                )
                track.sample_boundaries = list(item.get("sample_boundaries", []))
                track._normalize_boundaries()
                restored_tracks.append(track)

            self.project._tracks = restored_tracks
            self.track_selection_ranges.clear()
            for idx, selection in state.get("selections_by_index", {}).items():
                if 0 <= idx < len(restored_tracks):
                    self.track_selection_ranges[id(restored_tracks[idx])] = tuple(selection)

            self.stop_transport()
            selected_row = state.get("selected_row", -1)
            selected_track_id = None
            if isinstance(selected_row, int) and 0 <= selected_row < len(restored_tracks):
                selected_track_id = id(restored_tracks[selected_row])

            self.refresh_track_list(selected_track_id=selected_track_id)
            self.refresh_waveform_panel()
            self.sub_label.setText(f"{self.project.track_count()} track(s) in project")
            self.update_cut_controls()
        finally:
            self._restoring_history = False

    def push_undo_state(self):
        if self._restoring_history:
            return
        self.undo_stack.append(self.capture_editor_state())
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.update_cut_controls()

    def handle_undo(self):
        if not self.undo_stack:
            return
        current_state = self.capture_editor_state()
        state = self.undo_stack.pop()
        self.redo_stack.append(current_state)
        self.restore_editor_state(state)
        self.update_cut_controls()

    def handle_redo(self):
        if not self.redo_stack:
            return
        current_state = self.capture_editor_state()
        state = self.redo_stack.pop()
        self.undo_stack.append(current_state)
        self.restore_editor_state(state)
        self.update_cut_controls()

    def _selection_for_copy(self) -> tuple[AudioTrack, int, int] | None:
        selected_track = self.get_selected_track()
        if selected_track and id(selected_track) in self.track_selection_ranges:
            selection = self.track_selection_ranges[id(selected_track)]
            data = self._track_data_array(selected_track)
            if data.size == 0:
                return None
            start = int(np.clip(min(selection[0], selection[1]), 0.0, 1.0) * data.size)
            end = int(np.clip(max(selection[0], selection[1]), 0.0, 1.0) * data.size)
            if end > start:
                return selected_track, start, end

        for track in self.project.get_tracks():
            selection = self.track_selection_ranges.get(id(track))
            if not selection:
                continue
            data = self._track_data_array(track)
            if data.size == 0:
                continue
            start = int(np.clip(min(selection[0], selection[1]), 0.0, 1.0) * data.size)
            end = int(np.clip(max(selection[0], selection[1]), 0.0, 1.0) * data.size)
            if end > start:
                return track, start, end
        return None

    def handle_copy_selection(self):
        selected = self._selection_for_copy()
        if selected is None:
            return
        track, start, end = selected
        data = self._track_data_array(track)
        self.clipboard_audio = data[start:end].copy()
        self.clipboard_sample_rate = track.sample_rate
        self.sub_label.setText(f"Copied selection from {track.name}")
        self.update_cut_controls()

    def handle_paste_selection(self):
        if self.clipboard_audio.size == 0:
            return

        target_track = self.get_selected_track()
        if target_track is None:
            tracks = self.project.get_tracks()
            target_track = tracks[0] if tracks else None
        if target_track is None:
            return
        if target_track.sample_rate != self.clipboard_sample_rate:
            QMessageBox.warning(
                self,
                "Paste",
                "Clipboard sample rate does not match selected track sample rate.",
            )
            return

        target_data = self._track_data_array(target_track)
        selection = self.track_selection_ranges.get(id(target_track))
        if selection:
            base_index = int(np.clip(min(selection[0], selection[1]), 0.0, 1.0) * target_data.size)
        else:
            base_index = target_data.size

        insert_index = target_track.nearest_boundary(base_index)
        self.push_undo_state()
        if not target_track.insert_data(insert_index, self.clipboard_audio, as_new_segment=True):
            return

        new_end = insert_index + self.clipboard_audio.size
        total_len = max(1, len(target_track.data))
        self.track_selection_ranges.clear()
        self.track_selection_ranges[id(target_track)] = (
            insert_index / total_len,
            new_end / total_len,
        )
        self.stop_transport()
        for track in self.project.get_tracks():
            self.sync_waveform_for_track(track)
        self.sub_label.setText(f"Pasted into {target_track.name}")
        self.update_cut_controls()

    def _read_wav_file(self, file_path: str) -> tuple[np.ndarray, int]:
        with wave.open(file_path, "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            frames = wav_file.readframes(frame_count)

        if sample_width == 1:
            data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
            data = (data - 128.0) / 128.0
        elif sample_width == 2:
            data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        elif sample_width == 3:
            raw = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
            ints = (
                raw[:, 0].astype(np.int32)
                | (raw[:, 1].astype(np.int32) << 8)
                | (raw[:, 2].astype(np.int32) << 16)
            )
            sign_bit = 1 << 23
            ints = (ints ^ sign_bit) - sign_bit
            data = ints.astype(np.float32) / float(1 << 23)
        elif sample_width == 4:
            data = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")

        if channels > 1:
            data = data.reshape(-1, channels).mean(axis=1)

        return np.clip(data, -1.0, 1.0).astype(np.float32), sample_rate

    def _write_wav_file(self, file_path: str, data: np.ndarray, sample_rate: int):
        clipped = np.clip(np.asarray(data, dtype=np.float32), -1.0, 1.0)
        pcm = (clipped * 32767.0).astype(np.int16)
        with wave.open(file_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm.tobytes())

    def _render_project_mix(self) -> tuple[np.ndarray, int] | None:
        tracks = self.project.get_tracks()
        if not tracks:
            return None

        non_empty = [t for t in tracks if len(t.data) > 0]
        if not non_empty:
            return None

        sample_rate = non_empty[0].sample_rate
        max_len = max(len(t.data) for t in non_empty)
        mix = np.zeros(max_len, dtype=np.float32)

        for track in non_empty:
            if track.muted:
                continue
            track_data = np.asarray(track.data, dtype=np.float32).flatten() * float(track.volume)
            if len(track_data) < max_len:
                track_data = np.pad(track_data, (0, max_len - len(track_data)))
            mix += track_data

        max_abs = np.max(np.abs(mix)) if mix.size > 0 else 0.0
        if max_abs > 1.0:
            mix = mix / max_abs

        return mix.astype(np.float32), sample_rate

    def handle_insert_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Insert Audio File",
            "",
            "WAV Files (*.wav);;All Files (*.*)",
        )
        if not paths:
            return

        added_count = 0
        for path in paths:
            try:
                audio_data, sample_rate = self._read_wav_file(path)
            except Exception as exc:
                QMessageBox.warning(self, "Insert File", f"Failed to load {path}:\n{exc}")
                continue
            if added_count == 0:
                self.push_undo_state()

            base_name = Path(path).stem or f"Track {self.project.track_count() + 1}"
            track_name = self._generate_unique_track_name(base_name)
            track = AudioTrack(
                name=track_name,
                sample_rate=sample_rate,
                data=audio_data,
                file_path=Path(path),
            )

            add_use_case = AddTrackToProject(self.project)
            add_use_case.execute(track)
            added_count += 1

        if added_count == 0:
            return

        self.refresh_track_list()
        self.refresh_waveform_panel()
        self.sub_label.setText(f"{self.project.track_count()} track(s) in project")
        self.update_cut_controls()

    def save_project_to_path(self, file_path: str):
        payload = {
            "version": 1,
            "name": self.project.name,
            "tracks": [
                {
                    "name": track.name,
                    "sample_rate": track.sample_rate,
                    "data": self._track_data_array(track).tolist(),
                    "file_path": str(track.file_path) if track.file_path else None,
                    "volume": track.volume,
                    "muted": track.muted,
                    "sample_boundaries": list(track.sample_boundaries),
                }
                for track in self.project.get_tracks()
            ],
        }
        with open(file_path, "w", encoding="utf-8") as out_file:
            json.dump(payload, out_file)
        self.project_file_path = file_path
        self.sub_label.setText(f"Saved project: {os.path.basename(file_path)}")

    def handle_save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            self.project_file_path or "project.vcoreproj",
            "VibeCore Project (*.vcoreproj);;JSON Files (*.json)",
        )
        if not path:
            return
        self.save_project_to_path(path)

    def handle_save_project(self):
        if not self.project_file_path:
            self.handle_save_project_as()
            return
        self.save_project_to_path(self.project_file_path)

    def load_project_from_path(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as in_file:
            payload = json.load(in_file)

        tracks_payload = payload.get("tracks", [])
        restored_tracks: list[AudioTrack] = []
        for item in tracks_payload:
            track = AudioTrack(
                name=item["name"],
                sample_rate=int(item["sample_rate"]),
                data=np.asarray(item.get("data", []), dtype=np.float32),
                file_path=Path(item["file_path"]) if item.get("file_path") else None,
                volume=float(item.get("volume", 1.0)),
                muted=bool(item.get("muted", False)),
            )
            track.sample_boundaries = list(item.get("sample_boundaries", []))
            track._normalize_boundaries()
            restored_tracks.append(track)

        self.stop_transport()
        self.project._tracks = restored_tracks
        self.project.name = str(payload.get("name", "My Project"))
        self.track_selection_ranges.clear()
        self.project_file_path = file_path
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.refresh_track_list()
        self.refresh_waveform_panel()
        self.sub_label.setText(f"{self.project.track_count()} track(s) in project")
        self.update_cut_controls()

    def handle_open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "VibeCore Project (*.vcoreproj *.json);;All Files (*.*)",
        )
        if not path:
            return
        try:
            self.load_project_from_path(path)
        except Exception as exc:
            QMessageBox.warning(self, "Open Project", f"Failed to open project:\n{exc}")

    def handle_export_mix(self):
        rendered = self._render_project_mix()
        if rendered is None:
            QMessageBox.information(self, "Export Mix", "Nothing to export.")
            return
        mix_data, sample_rate = rendered

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Mix",
            "project_mix.wav",
            "WAV Files (*.wav)",
        )
        if not path:
            return
        try:
            self._write_wav_file(path, mix_data, sample_rate)
            self.sub_label.setText(f"Exported mix: {os.path.basename(path)}")
        except Exception as exc:
            QMessageBox.warning(self, "Export Mix", f"Failed to export mix:\n{exc}")

    def handle_delete_key(self):
        if self.current_edit_tool in (self.TOOL_SELECT, self.TOOL_NONE) and self.track_selection_ranges:
            self.handle_cut_selection()
            return
        self.handle_delete_track()

    def handle_cut_selection(self):
        if self.current_edit_tool not in (self.TOOL_SELECT, self.TOOL_NONE):
            return
        if not self.track_selection_ranges:
            return

        self.push_undo_state()
        changed = False
        for track in self.project.get_tracks():
            selection = self.track_selection_ranges.get(id(track))
            if not selection:
                continue

            data = self._track_data_array(track)
            if data.size == 0:
                continue

            start = int(np.clip(min(selection[0], selection[1]), 0.0, 1.0) * data.size)
            end = int(np.clip(max(selection[0], selection[1]), 0.0, 1.0) * data.size)
            if end <= start:
                continue

            track.cut_range(start, end)
            self.sync_waveform_for_track(track)
            changed = True

        if changed:
            self.stop_transport()
            self.track_selection_ranges.clear()
            for track in self.project.get_tracks():
                self.sync_waveform_for_track(track)
            self.sub_label.setText("Selection cut")
        self.update_cut_controls()

    def split_sample_at(self, track: AudioTrack, position: float):
        split_index = self._sample_index_from_normalized(track, position)
        self.push_undo_state()
        if track.split_sample_at(split_index):
            self.sync_waveform_for_track(track)
            self.sub_label.setText(f"Split sample marker added in {track.name}")
        else:
            self.sub_label.setText("Split sample marker ignored (edge or duplicate)")

    def split_track_at(self, track: AudioTrack, position: float):
        data = self._track_data_array(track)
        if data.size < 2:
            QMessageBox.information(self, "Split Tool", "Track is too short to split.")
            return

        split_index = self._sample_index_from_normalized(track, position)
        if split_index <= 0 or split_index >= data.size:
            QMessageBox.information(self, "Split Tool", "Click inside the waveform to split.")
            return

        self.push_undo_state()
        first_part = data[:split_index].copy()
        second_part = data[split_index:].copy()
        track.set_data(first_part, reset_boundaries=True)

        new_track_name = self._generate_unique_track_name(f"{track.name} (Part 2)")
        new_track = AudioTrack(
            name=new_track_name,
            sample_rate=track.sample_rate,
            data=second_part,
            file_path=track.file_path,
            volume=track.volume,
            muted=track.muted,
        )

        self.project.insert_track_after(track, new_track)

        self.track_selection_ranges.pop(id(track), None)
        self.sub_label.setText(f"{self.project.track_count()} track(s) in project")
        self.stop_transport()
        self.refresh_track_list(selected_track_id=id(track))
        self.refresh_waveform_panel()
        self.update_cut_controls()

    def cut_track_backward(self, track: AudioTrack, position: float):
        data = self._track_data_array(track)
        if data.size == 0:
            return
        cut_index = self._sample_index_from_normalized(track, position)
        clip_start = track.previous_boundary_before(cut_index)
        if cut_index <= clip_start:
            return
        self.push_undo_state()
        track.cut_range(clip_start, cut_index)
        self.track_selection_ranges.pop(id(track), None)
        self.stop_transport()
        self.sync_waveform_for_track(track)
        self.update_cut_controls()

    def cut_track_forward(self, track: AudioTrack, position: float):
        data = self._track_data_array(track)
        if data.size == 0:
            return
        cut_index = self._sample_index_from_normalized(track, position)
        if cut_index >= data.size:
            return
        cut_end = track.next_boundary_after(cut_index)
        self.push_undo_state()
        track.cut_range(cut_index, cut_end)
        self.track_selection_ranges.pop(id(track), None)
        self.stop_transport()
        self.sync_waveform_for_track(track)
        self.update_cut_controls()

    def handle_delete_track(self):
        selected_row = self.track_list.currentRow()
        if selected_row == -1:
            return

        # Find corresponding AudioTrack object
        item = self.track_list.item(selected_row)
        widget = self.track_list.itemWidget(item)
        
        if widget:
            # Extract track name from the label in the widget
            label = widget.layout().itemAt(0).widget()
            track_name = label.text()
        else:
            # Fallback for text items
            item_text = item.text()
            track_name = item_text.split(" (")[0]
        
        track_to_delete = next((t for t in self.project.get_tracks() if t.name == track_name), None)

        if not track_to_delete:
            QMessageBox.warning(self, "Error", "Track not found in project.")
            return

        self.push_undo_state()
        # Use DeleteTrackFromProject use case
        delete_use_case = DeleteTrackFromProject(self.project)
        delete_use_case.execute(track_to_delete)

        if id(track_to_delete) in self.transport_track_ids or id(track_to_delete) == self.transport_record_track_id:
            self.stop_transport()

        # Remove from sidebar
        self.track_selection_ranges.pop(id(track_to_delete), None)
        self.refresh_track_list()
        self.sub_label.setText(f"{self.project.track_count()} track(s) in project")
        self.refresh_waveform_panel()
        self.update_cut_controls()

    def handle_rename_track(self):
        selected_row = self.track_list.currentRow()
        if selected_row == -1:
            return

        item = self.track_list.item(selected_row)
        widget = self.track_list.itemWidget(item)
        
        if widget:
            # Extract track name from the label in the widget
            label = widget.layout().itemAt(0).widget()
            track_name = label.text()
        else:
            # Fallback for text items
            item_text = item.text()
            track_name = item_text.split(" (")[0]
        
        track_to_rename = next((t for t in self.project.get_tracks() if t.name == track_name), None)

        if not track_to_rename:
            QMessageBox.warning(self, "Error", "Track not found in project.")
            return

        # Ask user for new name
        new_name, ok = QInputDialog.getText(self, "Rename Track", "Enter new track name:", text=track_to_rename.name)
        if not ok or not new_name.strip():
            return

        try:
            self.push_undo_state()
            rename_use_case = RenameTrack(self.project)
            rename_use_case.execute(track_to_rename, new_name)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        # Update the label in the widget
        if widget:
            label.setText(track_to_rename.name)
        self.sync_waveform_for_track(track_to_rename)
    
    def get_selected_track(self):
        selected_row = self.track_list.currentRow()
        if selected_row == -1:
            return None

        item = self.track_list.item(selected_row)
        widget = self.track_list.itemWidget(item)
        
        if widget:
            # Extract track name from the label in the widget
            label = widget.layout().itemAt(0).widget()
            track_name = label.text()
        else:
            # Fallback for text items
            item_text = item.text()
            track_name = item_text.split(" (")[0]
        
        return next((t for t in self.project.get_tracks() if t.name == track_name), None)


    def handle_play(self):
        track = self.get_selected_track()
        if not track:
            print("No track selected")
            return
        
        print(f"Attempting to play {track.name}: muted={track.muted}, volume={track.volume}, data_len={len(track.data)}")
        
        if track.muted:
            print(f"Track {track.name} is muted, skipping playback")
            return
            
        if len(track.data) == 0:
            print(f"Track {track.name} has no data")
            return

        self.stop_transport()
        data_to_play = np.array(track.data, dtype="float32") * track.volume
        self.audio_engine.play(data_to_play, track.sample_rate)
        duration_seconds = len(track.data) / max(track.sample_rate, 1)
        self.start_transport("play_track", {id(track)}, duration_seconds)
        print(f"Playing {track.name}")

    
    def handle_play_project(self):
        if not self.project.get_tracks():
            QMessageBox.information(self, "Info", "No tracks to play.")
            return

        self.stop_transport()
        from audio_editor.use_cases.play_project import PlayProject
        play_use_case = PlayProject(self.audio_engine)
        play_use_case.execute(self.project.get_tracks())
        durations = [
            len(t.data) / max(t.sample_rate, 1)
            for t in self.project.get_tracks()
            if len(t.data) > 0
        ]
        max_duration = max(durations) if durations else 0.0
        track_ids = {id(t) for t in self.project.get_tracks()}
        self.start_transport("play_project", track_ids, max_duration)

    def handle_stop(self):
        self.audio_engine.stop()
        self.stop_transport()


    def handle_record_toggle(self):
        track = self.get_selected_track()
        if not track:
            return

        if not self.audio_engine.is_recording():
            self.stop_transport()
            start_use_case = StartRecording(self.audio_engine)
            start_use_case.execute(track.sample_rate)
            self.record_button.setText("■")
            self.record_button.setToolTip("Stop Recording")
            self.start_transport(
                "record",
                {id(track)},
                0.0,
                record_track_id=id(track),
                record_sample_rate=track.sample_rate,
            )
        else:
            self.push_undo_state()
            stop_use_case = StopRecording(self.audio_engine)
            stop_use_case.execute(track)
            self.record_button.setText("●")
            self.record_button.setToolTip("Record")
            self.sync_waveform_for_track(track)
            self.stop_transport()

            # Update the track name label (not needed for sample count since we use widgets now)
    
    def on_volume_changed(self, track, value):
        """Handle volume slider changes"""
        track.volume = value / 100
        print(f"{track.name} volume = {track.volume}")  # debug
    
    def on_mute_toggled(self, track, checked):
        """Handle mute checkbox toggle"""
        track.muted = checked
        print(f"{track.name} muted = {track.muted}")  # debug


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
