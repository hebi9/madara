from __future__ import annotations

import json
from pathlib import Path


CONFIG_FILE = Path(__file__).resolve().parent / "shortcuts.json"


class ShortcutConfig:
    DEFAULTS = {
        "play": "Ctrl+P",
        "stop": "Ctrl+Shift+P",
    }

    @classmethod
    def load(cls) -> dict[str, str]:
        values = dict(cls.DEFAULTS)
        if not CONFIG_FILE.exists():
            return values

        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return values

        for command in cls.DEFAULTS:
            shortcut = data.get(command)
            if isinstance(shortcut, str):
                values[command] = shortcut
        return values

    @classmethod
    def save(cls, shortcuts: dict[str, str]) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(shortcuts, file, indent=4, ensure_ascii=False)