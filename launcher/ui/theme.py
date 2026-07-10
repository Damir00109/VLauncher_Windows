APP_STYLESHEET = """
* {
    font-family: "Segoe UI", "Inter", sans-serif;
}

QMainWindow, QWidget {
    background: transparent;
    color: #e8edf7;
    font-size: 13px;
}

QWidget#panel {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 16px;
}

QLabel#panelTitle {
    color: #9aa8c0;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 2px 4px 10px 4px;
    background: transparent;
}

QLineEdit {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 12px 14px;
    background: rgba(0, 0, 0, 0.22);
    color: #f1f5ff;
    selection-background-color: #6d5ef7;
}

QLineEdit:focus {
    border: 1px solid rgba(124, 92, 255, 0.65);
    background: rgba(0, 0, 0, 0.3);
}

QLineEdit::placeholder {
    color: #7b879d;
}

QListWidget, QTextEdit, QTextBrowser {
    border: none;
    border-radius: 12px;
    padding: 6px;
    background: rgba(0, 0, 0, 0.18);
    color: #e8edf7;
    outline: none;
}

QListWidget::item {
    padding: 4px 6px;
    border-radius: 12px;
    min-height: 48px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(109, 94, 247, 0.45),
        stop:1 rgba(56, 189, 248, 0.22)
    );
    color: #ffffff;
}

QListWidget::item:hover {
    background: rgba(255, 255, 255, 0.06);
}

QPushButton {
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    background: rgba(255, 255, 255, 0.08);
    color: #e8edf7;
}

QPushButton:hover {
    background: rgba(255, 255, 255, 0.13);
}

QPushButton:disabled {
    color: #667085;
    background: rgba(255, 255, 255, 0.03);
}

QGroupBox {
    font-weight: 600;
    border: none;
    margin-top: 14px;
    padding: 4px 0 0 0;
    background: transparent;
    color: #9aa8c0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 0;
    padding: 0;
    color: #9aa8c0;
}

QProgressBar {
    border: none;
    border-radius: 10px;
    text-align: center;
    background: rgba(0, 0, 0, 0.25);
    min-height: 10px;
}

QProgressBar::chunk {
    border-radius: 10px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c5cff,
        stop:1 #38bdf8
    );
}

QMenu {
    background: #1b2130;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 18px;
    border-radius: 8px;
}

QMenu::item:selected {
    background: rgba(124, 92, 255, 0.35);
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 2px 4px 0;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.16);
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.26);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    height: 0;
}
"""

LAUNCH_BUTTON_STYLE = """
QPushButton {
    font-weight: 800;
    font-size: 16px;
    letter-spacing: 0.8px;
    padding: 14px;
    color: #ffffff;
    border: none;
    border-radius: 14px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c5cff,
        stop:1 #38bdf8
    );
}
QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #9178ff,
        stop:1 #5ec8ff
    );
}
QPushButton:disabled {
    color: #667085;
    background: rgba(255, 255, 255, 0.05);
}
"""

LAUNCH_RUNNING_BUTTON_STYLE = """
QPushButton {
    font-weight: 700;
    font-size: 15px;
    letter-spacing: 0.4px;
    padding: 14px;
    color: #8b97ad;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.04);
}
QPushButton:disabled {
    color: #8b97ad;
    background: rgba(255, 255, 255, 0.04);
}
"""

STOP_BUTTON_STYLE = """
QPushButton {
    background: #e5484d;
    border: 1px solid #ff6b6b;
    border-radius: 14px;
    padding: 0;
}
QPushButton:hover {
    background: #f2555a;
    border-color: #ff8585;
}
QPushButton:pressed {
    background: #c73e42;
}
"""

PROFILE_BUTTON_STYLE = """
QPushButton {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 6px 14px 6px 10px;
    font-weight: 600;
    color: #eef2ff;
}
QPushButton:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(124, 92, 255, 0.45);
}
QPushButton:pressed {
    background: rgba(255, 255, 255, 0.14);
}
"""

ICON_BUTTON_STYLE = """
QPushButton {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 0;
}
QPushButton:hover {
    background: rgba(255, 255, 255, 0.11);
    border-color: rgba(124, 92, 255, 0.4);
}
QPushButton:pressed {
    background: rgba(255, 255, 255, 0.14);
}
QPushButton:disabled {
    background: rgba(255, 255, 255, 0.03);
    border-color: rgba(255, 255, 255, 0.05);
}
"""

LOGIN_BUTTON_STYLE = """
QPushButton {
    font-weight: 700;
    font-size: 14px;
    padding: 12px;
    color: #ffffff;
    border: none;
    border-radius: 12px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c5cff,
        stop:1 #5b8def
    );
}
QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #9178ff,
        stop:1 #6fa0ff
    );
}
QPushButton:disabled {
    color: #667085;
    background: rgba(255, 255, 255, 0.05);
}
"""

GHOST_BUTTON_STYLE = """
QPushButton {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    color: #c6d0e4;
    padding: 8px 14px;
}
QPushButton:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(124, 92, 255, 0.35);
}
"""

ACCENT_BUTTON_STYLE = """
QPushButton {
    background: rgba(124, 92, 255, 0.22);
    border: 1px solid rgba(124, 92, 255, 0.45);
    border-radius: 12px;
    color: #f0eaff;
    font-weight: 600;
    padding: 10px 16px;
}
QPushButton:hover {
    background: rgba(124, 92, 255, 0.34);
}
QPushButton:disabled {
    color: #667085;
    background: rgba(255, 255, 255, 0.03);
    border-color: rgba(255, 255, 255, 0.05);
}
"""

GEAR_BUTTON_STYLE = ICON_BUTTON_STYLE

CHECKBOX_STYLE = """
QCheckBox {
    color: #eef2ff;
    spacing: 10px;
    background: transparent;
    padding: 8px 10px;
    border-radius: 8px;
}
QCheckBox:hover {
    background: rgba(124, 92, 255, 0.12);
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    background: rgba(0, 0, 0, 0.2);
}
QCheckBox::indicator:hover {
    border-color: rgba(124, 92, 255, 0.5);
}
QCheckBox::indicator:checked {
    background: #7c5cff;
    border-color: #9178ff;
}
QCheckBox::indicator:checked:hover {
    background: #9178ff;
    border-color: #a890ff;
}
"""
