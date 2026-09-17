from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QUrl

from app.sources.base_source import BaseSource


@dataclass
class VideoSource(BaseSource):
    path: str = ""
    loop: bool = True

    @classmethod
    def create(cls, path: str, name: str | None = None) -> VideoSource:
        return cls(
            name=name or "Video",
            x=0,
            y=0,
            width=640,
            height=360,
            path=path,
        )

    def media_url(self) -> QUrl:
        return QUrl.fromLocalFile(self.path)
