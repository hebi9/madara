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
    ) -> None:

        self.stop()

        screens = QGuiApplication.screens()

        scene = monitor_view.program_scene

        for screen in screens:

            if screen.name() not in monitor_names:
                continue

            monitor_item = (
                monitor_view.get_program_monitor_item(
                    screen.name()
                )
            )

            if monitor_item is None:
                continue

            window = PlaybackWindow(
                screen=screen,
                scene=scene,
                monitor_item=monitor_item,
            )

            self.windows.append(
                window
            )

            window.destroyed.connect(
                self._window_destroyed
            )

            window.show_playback()

    def stop(self) -> None:

        windows = list(self.windows)
        self.windows.clear()

        for window in windows:

            if not isValid(window) or not callable(
                getattr(window, "close", None)
            ):
                continue

            window.close()
            window.deleteLater()

    def _window_destroyed(self, window) -> None:
        if window in self.windows:
            self.windows.remove(window)

    @property
    def is_playing(self) -> bool:

        return bool(
            self.windows
        )