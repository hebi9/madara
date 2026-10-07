from __future__ import annotations

import json
from pathlib import Path


CONFIG_FILE = Path(__file__).resolve().parent / "audio_config.json"


class AudioConfig:
    @staticmethod
    def load() -> str | None:
        if not CONFIG_FILE.exists():
            return None
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError, TypeError):
            return None

        value = data.get("output_device")
        return str(value) if value else None

    @staticmethod
    def save(output_device: str | None) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                {"output_device": output_device},
                file,
                indent=4,
                ensure_ascii=False,
            )
