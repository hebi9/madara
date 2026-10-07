from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import QFrame, QGraphicsView


class PlaybackWindow(QGraphicsView):

    def __init__(
        self,
        screen,
        scene,
        monitor_item,
        audio_device_name: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(scene, parent)

        self.screen = screen
        self.playback_scene = scene
        self.monitor_item = monitor_item
        self.audio_device_name = audio_device_name

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setBackgroundBrush(Qt.GlobalColor.black)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setInteractive(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate
        )

        self._configure_audio_output()
        self._configure_geometry()

    def _configure_audio_output(self) -> None:
        if not self.audio_device_name:
            return

        for device in QMediaDevices.audioOutputs():
            if device.description() == self.audio_device_name:
                for item in self.playback_scene.items():
                    setter = getattr(item, "set_audio_output", None)
                    if setter is not None:
                        setter(device)
                return

    def _configure_geometry(self) -> None:
        self.setGeometry(self.screen.geometry())

    def _fit_scene(self) -> None:
        width = float(self.monitor_item.workspace.width) * 0.15
        height = float(self.monitor_item.workspace.height) * 0.15
        self.fitInView(
            QRectF(0, 0, width, height),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_scene()

    def show_playback(self) -> None:
        self._configure_geometry()
        self.show()
        self.raise_()
        self.activateWindow()
        self._fit_scene()
        self.start_videos()

    def start_videos(self) -> None:
        self._configure_audio_output()
        for item in self.playback_scene.items():
            starter = getattr(item, "start_from_zero", None)
            if starter is not None:
                starter()

    def _stop_videos(self) -> None:
        for item in self.playback_scene.items():
            stopper = getattr(item, "stop_playback", None)
            if stopper is not None:
                stopper()

    def closeEvent(self, event) -> None:
        self._stop_videos()
        super().closeEvent(event)
