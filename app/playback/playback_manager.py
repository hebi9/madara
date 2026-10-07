from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from shiboken6 import isValid

from app.playback.playback_window import PlaybackWindow


class PlaybackManager:

    def __init__(self) -> None:
        self.windows: list[PlaybackWindow] = []

    def play(
        self,
        monitor_view,
        monitor_names: set[str],
        audio_device_name: str | None = None,
    ) -> None:
        self.stop()

        # El stop() usa deleteLater(). Procesamos esos eventos antes de crear
        # una nueva generación de ventanas para evitar que una reproducción
        # anterior interfiera con el siguiente Play.
        app = QGuiApplication.instance()
        if app is not None:
            app.processEvents()

        screens = QGuiApplication.screens()

        for screen in screens:
            if screen.name() not in monitor_names:
                continue

            monitor_item = monitor_view.get_program_monitor_item(
                screen.name()
            )
            scene = monitor_view.get_program_scene(screen.name())

            if monitor_item is None or scene is None:
                continue

            window = PlaybackWindow(
                screen=screen,
                scene=scene,
                monitor_item=monitor_item,
                audio_device_name=audio_device_name,
            )

            self.windows.append(window)
            window.destroyed.connect(self._window_destroyed)
            window.show_playback()

    def stop(self) -> None:
        windows = list(self.windows)
        self.windows.clear()

        for window in windows:
            if not isValid(window):
                continue

            window.close()
            window.deleteLater()

        app = QGuiApplication.instance()
        if app is not None:
            app.processEvents()

    def _window_destroyed(self, window) -> None:
        if window in self.windows:
            self.windows.remove(window)

    @property
    def is_playing(self) -> bool:
        return bool(self.windows)
