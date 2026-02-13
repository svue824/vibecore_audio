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
}

QListWidget::item {
    padding: 8px;
    border-radius: 6px;
}

QListWidget::item:selected {
    background-color: #2A2A2A;
}
"""
