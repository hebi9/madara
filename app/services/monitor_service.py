from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication


@dataclass(frozen=True)
class MonitorInfo:
    index: int
    name: str
    geometry: QRect
    available_geometry: QRect
    is_primary: bool

    @property
    def display_name(self) -> str:
        primary_suffix = " (principal)" if self.is_primary else ""
        return f"{self.name}{primary_suffix} - {self.geometry.width()}x{self.geometry.height()}"


class MonitorService:
    @staticmethod
    def list_monitors() -> list[MonitorInfo]:
        app = QGuiApplication.instance() or QGuiApplication([])
        screens = app.screens()

        monitors: list[MonitorInfo] = []
        for index, screen in enumerate(screens):
            monitors.append(
                MonitorInfo(
                    index=index,
                    name=screen.name() or f"Monitor {index + 1}",
                    geometry=screen.geometry(),
                    available_geometry=screen.availableGeometry(),
                    is_primary=screen is app.primaryScreen(),
                )
            )

        return monitors
