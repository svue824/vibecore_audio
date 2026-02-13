import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt

from audio_editor.use_cases.create_empty_track import CreateEmptyTrack
from audio_editor.ui.styles import DARK_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VibeCore Audio")
        self.setMinimumSize(500, 300)

        # Apply dark style
        self.setStyleSheet(DARK_STYLE)

        # Use case instance
        self.create_track_use_case = CreateEmptyTrack()

        # Central container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        central_widget.setLayout(layout)

        # Title
        self.title_label = QLabel("VibeCore Audio")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)

        # Subtitle
        self.sub_label = QLabel("Create and manipulate audio tracks")
        self.sub_label.setObjectName("subLabel")
        self.sub_label.setAlignment(Qt.AlignCenter)

        # Button
        self.create_button = QPushButton("Create Empty Track")
        self.create_button.clicked.connect(self.handle_create_track)

        layout.addWidget(self.title_label)
        layout.addWidget(self.sub_label)
        layout.addWidget(self.create_button)

    def handle_create_track(self):
        track = self.create_track_use_case.execute(
            name="New Track",
            duration_seconds=2.0,
            sample_rate=44100,
        )

        self.sub_label.setText(
            f"Created '{track.name}' | {len(track.data)} samples"
        )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
