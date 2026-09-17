from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QWidget


class PlaybackWindow(QWidget):

    FRAME_INTERVAL_MS = 33  # ~30 FPS, suficiente para video fluido

    def __init__(
        self,
        screen,
        scene,
        monitor_item,
        parent=None,
    ) -> None:

        super().__init__(parent)

        self.screen = screen
        self.scene = scene
        self.monitor_item = monitor_item

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose
        )

        self.setStyleSheet(
            "background-color: black;"
        )

        self._configure_geometry()

        # Redibuja periódicamente para reflejar contenido en vivo
        # (video, páginas web, etc.), no solo un fotograma estático.
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(self.FRAME_INTERVAL_MS)
        self._refresh_timer.timeout.connect(self.render_scene)

    def _configure_geometry(self) -> None:

        geometry = self.screen.geometry()

        self.setGeometry(
            geometry
        )

    def render_scene(self) -> None:

        monitor_rect = (
            self.monitor_item.sceneBoundingRect()
        )

        width = self.screen.geometry().width()
        height = self.screen.geometry().height()

        image = QImage(
            width,
            height,
            QImage.Format.Format_RGB32,
        )

        image.fill(
            Qt.GlobalColor.black
        )

        painter = QPainter(image)

        self.scene.render(
            painter,
            QRectF(
                0,
                0,
                width,
                height,
            ),
            monitor_rect,
            Qt.AspectRatioMode.IgnoreAspectRatio,
        )

        painter.end()

        self._frame = image

        self.update()

    def paintEvent(self, event) -> None:

        if not hasattr(self, "_frame"):
            return

        painter = QPainter(self)

        painter.drawImage(
            0,
            0,
            self._frame,
        )

        painter.end()

    def show_playback(self) -> None:

        self._configure_geometry()

        self.render_scene()

        self.show()

        self.raise_()

        self.activateWindow()

        self._refresh_timer.start()

    def closeEvent(self, event) -> None:

        self._refresh_timer.stop()

        super().closeEvent(event)