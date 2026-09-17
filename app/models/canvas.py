from __future__ import annotations

from dataclasses import dataclass

from app.services.monitor_service import MonitorInfo


@dataclass
class Canvas:
    monitor_name: str
    width: int
    height: int

    @classmethod
    def from_monitor(
        cls,
        monitor: MonitorInfo,
    ) -> Canvas:

        return cls(
            monitor_name=monitor.name,
            width=monitor.geometry.width(),
            height=monitor.geometry.height(),
        )