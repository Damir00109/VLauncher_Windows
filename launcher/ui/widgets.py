from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


def create_panel(title: str = "") -> tuple[QWidget, QVBoxLayout]:
    panel = QWidget()
    panel.setObjectName("panel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(10)
    if title:
        header = QLabel(title)
        header.setObjectName("panelTitle")
        layout.addWidget(header)
    return panel, layout
