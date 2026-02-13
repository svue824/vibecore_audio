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
)
from PySide6.QtCore import Qt

from audio_editor.use_cases.create_empty_track import CreateEmptyTrack
from audio_editor.ui.styles import DARK_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VibeCore Audio")
        self.setMinimumSize(800, 500)

        self.setStyleSheet(DARK_STYLE)

        self.create_track_use_case = CreateEmptyTrack()

        # Application state
        self.tracks = []

        # ===== Central Widget =====
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # ===== Left Sidebar =====
        self.track_list = QListWidget()
        self.track_list.setFixedWidth(220)
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

        # Subtitle
        self.sub_label = QLabel("Create and manage audio tracks")
        self.sub_label.setObjectName("subLabel")
        self.sub_label.setAlignment(Qt.AlignCenter)

        # Button
        self.create_button = QPushButton("Create Empty Track")
        self.create_button.clicked.connect(self.handle_create_track)

        right_layout.addWidget(self.title_label)
        right_layout.addWidget(self.sub_label)
        right_layout.addWidget(self.create_button)

    def handle_create_track(self):
        track_number = len(self.tracks) + 1

        track = self.create_track_use_case.execute(
            name=f"Track {track_number}",
            duration_seconds=2.0,
            sample_rate=44100,
        )

        self.tracks.append(track)

        # Add to UI list
        item_text = f"{track.name} ({len(track.data)} samples)"
        QListWidgetItem(item_text, self.track_list)

        self.sub_label.setText(f"{len(self.tracks)} track(s) in project")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
