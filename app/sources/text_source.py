from __future__ import annotations

from dataclasses import dataclass

from app.sources.base_source import BaseSource


@dataclass
class TextSource(BaseSource):
    text: str = "Texto"
    font_size: int = 32
    color: str = "#000000"

    @classmethod
    def create(
        cls,
        text: str = "Texto",
    ) -> TextSource:

        return cls(
            name="Texto",
            x=100,
            y=100,
            width=400,
            height=100,
            text=text,
            font_size=32,
            color="#000000",
        )