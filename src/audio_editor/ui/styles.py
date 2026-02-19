DARK_STYLE = """
QMainWindow {
    background-color: #07090E;
}

QWidget {
    background-color: #07090E;
    color: #ECF2FF;
    font-family: "Segoe UI", "Trebuchet MS", "Verdana";
    font-size: 14px;
}

QPushButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #1B2333,
        stop: 1 #0E1422
    );
    border: 1px solid #2E3E5E;
    border-radius: 11px;
    padding: 10px 18px;
    font-weight: 600;
    color: #E9F1FF;
}

QPushButton:hover {
    border: 1px solid #4A79D9;
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #263A5E,
        stop: 1 #17253D
    );
}

QPushButton:pressed {
    background: #1A2842;
    border: 1px solid #5A8AED;
}

QPushButton:disabled {
    background: #0D121D;
    color: #5B6780;
    border: 1px solid #1C2538;
}

QWidget#actionBarHost {
    background: transparent;
}

QWidget#actionStrip {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #121A2A,
        stop: 0.55 #0D1424,
        stop: 1 #0B111F
    );
    border: 1px solid #2C3D5F;
    border-radius: 14px;
}

QFrame#actionDivider {
    background-color: #25334E;
    min-width: 1px;
    max-width: 1px;
    margin: 4px 6px;
}

QPushButton#actionButton,
QPushButton#deleteButton,
QToolButton#fileButton {
    min-height: 34px;
    padding: 7px 10px;
    border-radius: 9px;
}

QPushButton#transportButton {
    min-height: 34px;
    min-width: 46px;
    max-width: 46px;
    padding: 4px 0;
    font-size: 18px;
    font-weight: 700;
    border-radius: 9px;
    color: #EAF2FF;
}

QPushButton#recordButton {
    min-height: 34px;
    min-width: 46px;
    max-width: 46px;
    padding: 4px 0;
    font-size: 18px;
    font-weight: 700;
    color: #FFD9D9;
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #5F1A2B,
        stop: 1 #3E0D1A
    );
    border: 1px solid #B84965;
    border-radius: 9px;
}

QPushButton#recordButton:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #7B253A,
        stop: 1 #511726
    );
    border: 1px solid #E66E8C;
}

QPushButton#recordButton:pressed {
    background: #5A192A;
}

QToolButton#fileButton {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #1D283D,
        stop: 1 #121A2A
    );
    border: 1px solid #2F4267;
    padding: 7px 24px 7px 10px;
}

QToolButton#fileButton::menu-indicator {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 10px;
}

QComboBox#toolPicker {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #1D283D,
        stop: 1 #121A2A
    );
    border: 1px solid #2F4267;
    border-radius: 9px;
    min-height: 34px;
    min-width: 136px;
    padding: 6px 30px 6px 10px;
}

QComboBox#toolPicker::drop-down {
    border: none;
    width: 24px;
}

QComboBox#toolPicker QAbstractItemView {
    background-color: #111B30;
    border: 1px solid #2F4267;
    selection-background-color: #2B4E86;
}

QLabel#actionLabel {
    font-size: 13px;
    color: #BFD0EE;
    font-weight: 600;
    padding: 0 4px;
}

QLabel#titleLabel {
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel#subLabel {
    font-size: 13px;
    color: #90A3C8;
}

QListWidget {
    background-color: #0D1424;
    border-right: 1px solid #243754;
    padding: 0px;
    font-size: 14px;
}
QListWidget::item {
    padding: 0px;
    border-radius: 6px;
}

QListWidget::item:selected {
    background-color: #223856;
    color: #FFFFFF;
}

QWidget#trackRow {
    background-color: #0B101C;
    border: 1px solid transparent;
    border-radius: 8px;
}

QWidget#trackRow[selected="true"] {
    background-color: #1A2C48;
    border: 1px solid #4B73AE;
}

QLineEdit#trackNameEditor {
    color: #EAF2FF;
    font-weight: 700;
    font-size: 13px;
    background: #0C1527;
    border: 1px solid #3D5B8F;
    border-radius: 6px;
    padding: 4px 8px;
}

QLineEdit#trackNameEditor:focus {
    border: 1px solid #79A9FF;
    background: #0F1C34;
}

QCheckBox#trackMuteControl {
    color: #C8D6F1;
    spacing: 6px;
    min-width: 56px;
    background: #0C1527;
    border: 1px solid #3D5B8F;
    border-radius: 6px;
    padding: 3px 8px 3px 8px;
}

QCheckBox#trackMuteControl::indicator {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid #4A6594;
    background: #111B30;
}

QCheckBox#trackMuteControl::indicator:checked {
    background: #6B8FD8;
    border: 1px solid #8EB1F5;
}

QSlider#trackVolumeSlider::groove:horizontal {
    border: 1px solid #2B4067;
    height: 6px;
    background: #0E1628;
    border-radius: 3px;
}

QSlider#trackVolumeSlider::sub-page:horizontal {
    background: #4C7EDB;
    border-radius: 3px;
}

QSlider#trackVolumeSlider::handle:horizontal {
    background: #BFD6FF;
    border: 1px solid #E3EEFF;
    width: 12px;
    margin: -5px 0;
    border-radius: 6px;
}

QListWidget#waveformList {
    background-color: #07090E;
    border: none;
    padding: 0px;
}

QListWidget#waveformList::item {
    padding: 0px;
    border-radius: 6px;
}

QListWidget#waveformList::item:selected {
    background-color: #1A2D4A;
}

QWidget#waveformRow {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #090E1A,
        stop: 0.495 #090E1A,
        stop: 0.5 #2A426D,
        stop: 0.505 #090E1A,
        stop: 1 #090E1A
    );
    border-top: 1px solid #253A5A;
    border-bottom: 1px solid #253A5A;
    border-left: 1px solid transparent;
    border-right: 1px solid transparent;
    border-radius: 8px;
}

QWidget#waveformRow[selected="true"] {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #1C3255,
        stop: 0.495 #1C3255,
        stop: 0.5 #67A3FF,
        stop: 0.505 #1C3255,
        stop: 1 #1C3255
    );
    border-top: 1px solid #4E78B7;
    border-bottom: 1px solid #4E78B7;
    border-left: 1px solid #4E78B7;
    border-right: 1px solid #4E78B7;
}
"""
