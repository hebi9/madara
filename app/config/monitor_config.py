from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QPointF


CONFIG_FILE = Path(__file__).resolve().parent / "monitor_layout.json"


class MonitorConfig:

    @staticmethod
    def load() -> tuple[set[str], dict[str, QPointF]]:
        if not CONFIG_FILE.exists():
            return set(), {}

        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return set(), {}

        active_monitors = set(data.get("active_monitors", []))

        positions = {}

        for name, position in data.get("positions", {}).items():
            try:
                positions[name] = QPointF(
                    float(position["x"]),
                    float(position["y"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

        return active_monitors, positions

    @staticmethod
    def save(
        active_monitors: set[str],
        positions: dict[str, QPointF],
    ) -> None:

        CONFIG_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "active_monitors": sorted(active_monitors),
            "positions": {
                name: {
                    "x": position.x(),
                    "y": position.y(),
                }
                for name, position in positions.items()
            },
        }

        with CONFIG_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )