import sys
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
)
from PySide6.QtCore import Qt

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
    def __init__(self):
        super().__init__()
        self.audio_engine = AudioEngine()

        self.setWindowTitle("VibeCore Audio")
        self.setMinimumSize(800, 500)
        self.setStyleSheet(DARK_STYLE)

        # ===== Domain State =====
        self.project = Project("My Project")

        # ===== Central Widget =====
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # ===== Left Sidebar =====
        self.track_list = QListWidget()
        self.track_list.setFixedWidth(220)

        # ----- NEW: Enable drag-and-drop reordering -----
        self.track_list.setDragDropMode(QListWidget.InternalMove)
        self.track_list.setDefaultDropAction(Qt.MoveAction)
        self.track_list.model().rowsMoved.connect(self.handle_reorder_tracks)

        self.track_list.itemSelectionChanged.connect(self.on_track_selected)
        main_layout.addWidget(self.track_list)

        # ===== Right Content Area =====
        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.setSpacing(20)
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

        self.waveform_widget = WaveformWidget()
        right_layout.addWidget(self.waveform_widget)

        # Buttons
        self.add_button = QPushButton("Add Track")
        self.add_button.clicked.connect(self.handle_add_track)
        right_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("Delete Track")
        self.delete_button.clicked.connect(self.handle_delete_track)
        self.delete_button.setEnabled(False)
        self.delete_button.setObjectName("deleteButton")
        right_layout.addWidget(self.delete_button)

        self.rename_button = QPushButton("Rename Track")
        self.rename_button.clicked.connect(self.handle_rename_track)
        right_layout.addWidget(self.rename_button)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.handle_play)
        right_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.handle_stop)
        right_layout.addWidget(self.stop_button)

        self.record_button = QPushButton("Record")
        self.record_button.clicked.connect(self.handle_record_toggle)
        right_layout.addWidget(self.record_button)

        self.play_button = QPushButton("Play Project")
        self.play_button.clicked.connect(self.handle_play_project)
        right_layout.addWidget(self.play_button)


    from PySide6.QtCore import Slot

    @Slot()
    def handle_reorder_tracks(self):
        """Sync project tracks with the current sidebar order."""
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

    # ----- Handlers -----
    def handle_add_track(self):
        track_number = self.project.track_count() + 1
        new_track = AudioTrack(
            name=f"Track {track_number}",
            sample_rate=44100,
            data=np.zeros(44100, dtype=np.float32)  # 1 second of silence
        )

        # Use AddTrackToProject use case
        add_use_case = AddTrackToProject(self.project)
        add_use_case.execute(new_track)

        # Mute box & vol slider
        self.add_track_ui_item(new_track)

        # Update subtitle
        self.sub_label.setText(f"{self.project.track_count()} track(s) in project")

    # When adding a track, create a container widget
    def add_track_ui_item(self, track):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

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


    def on_track_selected(self):
        selected = self.track_list.currentRow()
        self.delete_button.setEnabled(selected != -1)
        track = self.get_selected_track()
        self.waveform_widget.set_audio_data(track.data if track else None)

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

        # Use DeleteTrackFromProject use case
        delete_use_case = DeleteTrackFromProject(self.project)
        delete_use_case.execute(track_to_delete)

        # Remove from sidebar
        self.track_list.takeItem(selected_row)
        self.sub_label.setText(f"{self.project.track_count()} track(s) in project")

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
            rename_use_case = RenameTrack(self.project)
            rename_use_case.execute(track_to_rename, new_name)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        # Update the label in the widget
        if widget:
            label.setText(track_to_rename.name)
    
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
            
        data_to_play = np.array(track.data, dtype="float32") * track.volume
        self.audio_engine.play(data_to_play, track.sample_rate)
        print(f"Playing {track.name}")

    
    def handle_play_project(self):
        if not self.project.get_tracks():
            QMessageBox.information(self, "Info", "No tracks to play.")
            return

        from audio_editor.use_cases.play_project import PlayProject
        play_use_case = PlayProject(self.audio_engine)
        play_use_case.execute(self.project.get_tracks())

    def handle_stop(self):
        self.audio_engine.stop()


    def handle_record_toggle(self):
        track = self.get_selected_track()
        if not track:
            return

        if not self.audio_engine.is_recording():
            start_use_case = StartRecording(self.audio_engine)
            start_use_case.execute(track.sample_rate)
            self.record_button.setText("Stop Recording")
        else:
            stop_use_case = StopRecording(self.audio_engine)
            stop_use_case.execute(track)
            self.record_button.setText("Record")
            self.waveform_widget.set_audio_data(track.data)

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
