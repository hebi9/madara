from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class CanvasWidget(QFrame):
    def __init__(self, monitor_name: str, width: int, height: int, parent=None) -> None:
        super().__init__(parent)

        self.monitor_name = monitor_name
        self.canvas_width = width
        self.canvas_height = height

        self.setMinimumSize(200, 120)
        self.setStyleSheet("""
            QFrame {
                background-color: #181818;
                border: 1px solid #444444;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(monitor_name)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        resolution = QLabel(f"{width} × {height}")
        resolution.setAlignment(Qt.AlignmentFlag.AlignCenter)
        resolution.setStyleSheet("color: #aaaaaa;")

        layout.addWidget(title)
        layout.addWidget(resolution)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))