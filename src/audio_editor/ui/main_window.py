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
)
from PySide6.QtCore import Qt

from audio_editor.domain.audio_track import AudioTrack
from audio_editor.domain.project import Project
from audio_editor.use_cases.add_track_to_project import AddTrackToProject
from audio_editor.use_cases.delete_track_from_project import DeleteTrackFromProject
from audio_editor.ui.styles import DARK_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

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

        # Subtitle / Track count
        self.sub_label = QLabel("Create and manage audio tracks")
        self.sub_label.setObjectName("subLabel")
        self.sub_label.setAlignment(Qt.AlignCenter)

        # Buttons
        self.add_button = QPushButton("Add Track")
        self.add_button.clicked.connect(self.handle_add_track)

        self.delete_button = QPushButton("Delete Track")
        self.delete_button.clicked.connect(self.handle_delete_track)
        self.delete_button.setEnabled(False)
        self.delete_button.setObjectName("deleteButton")

        right_layout.addWidget(self.title_label)
        right_layout.addWidget(self.sub_label)
        right_layout.addWidget(self.add_button)
        right_layout.addWidget(self.delete_button)

    # ----- Handlers -----
    def handle_add_track(self):
        track_number = self.project.track_count() + 1
        new_track = AudioTrack(name=f"Track {track_number}", sample_rate=44100, data=[])

        # Use AddTrackToProject use case
        add_use_case = AddTrackToProject(self.project)
        add_use_case.execute(new_track)

        # Update sidebar
        item_text = f"{new_track.name} ({len(new_track.data)} samples)"
        QListWidgetItem(item_text, self.track_list)
        self.sub_label.setText(f"{self.project.track_count()} track(s) in project")

    def on_track_selected(self):
        selected = self.track_list.currentRow()
        self.delete_button.setEnabled(selected != -1)

    def handle_delete_track(self):
        selected_row = self.track_list.currentRow()
        if selected_row == -1:
            return

        # Find corresponding AudioTrack object
        item_text = self.track_list.item(selected_row).text()
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


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
