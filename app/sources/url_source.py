from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QUrl

from app.sources.base_source import BaseSource


@dataclass
class UrlSource(BaseSource):
    url: str = ""

    @classmethod
    def create(cls, url: str, name: str | None = None) -> UrlSource:
        return cls(
            name=name or "Internet",
            x=0,
            y=0,
            width=800,
            height=450,
            url=url,
        )

    def web_url(self) -> QUrl:
        return QUrl.fromUserInput(self.url)
