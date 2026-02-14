DARK_STYLE = """
QMainWindow {
    background-color: #111111;
}

QWidget {
    background-color: #111111;
    color: #EAEAEA;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
    font-size: 14px;
}

QPushButton {
    background-color: #1F1F1F;
    border: 1px solid #2A2A2A;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2A2A2A;
}

QPushButton:pressed {
    background-color: #333333;
}

QPushButton:disabled {
    background-color: #1A1A1A;
    color: #555555;
    border: 1px solid #2A2A2A;
}

QWidget#actionBarHost {
    background: transparent;
}

QWidget#actionStrip {
    background-color: #151515;
    border: 1px solid #2A2A2A;
    border-radius: 14px;
}

QFrame#actionDivider {
    background-color: #2B2B2B;
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
}

QPushButton#recordButton {
    min-height: 34px;
    min-width: 46px;
    max-width: 46px;
    padding: 4px 0;
    font-size: 18px;
    font-weight: 700;
    color: #FF5252;
    background-color: #1C1C1C;
    border: 1px solid #4A1F1F;
    border-radius: 9px;
}

QPushButton#recordButton:hover {
    background-color: #252020;
}

QToolButton#fileButton {
    background-color: #1C1C1C;
    border: 1px solid #2A2A2A;
    padding: 7px 24px 7px 10px;
}

QToolButton#fileButton::menu-indicator {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 10px;
}

QComboBox#toolPicker {
    background-color: #1C1C1C;
    border: 1px solid #2A2A2A;
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
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    selection-background-color: #2A2A2A;
}

QLabel#actionLabel {
    font-size: 13px;
    color: #C9C9C9;
    font-weight: 600;
    padding: 0 4px;
}

QLabel#titleLabel {
    font-size: 20px;
    font-weight: 600;
    color: #FFFFFF;
}

QLabel#subLabel {
    font-size: 13px;
    color: #888888;
}

QListWidget {
    background-color: #161616;
    border-right: 1px solid #2A2A2A;
    padding: 10px;
    font-size: 14px;
}
QListWidget::item {
    padding: 8px;
    border-radius: 6px;
}

QListWidget::item:selected {
    background-color: #2A2A2A;
    color: #FFFFFF;
}
"""
