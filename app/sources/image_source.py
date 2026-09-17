from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QImageReader, QPixmap

from app.sources.base_source import BaseSource


@dataclass
class ImageSource(BaseSource):
    path: str = ""

    @classmethod
    def create(
        cls,
        path: str,
        name: str | None = None,
    ) -> ImageSource:

        reader = QImageReader(path)
        image_size = reader.size()

        if image_size.isValid():
            width = image_size.width()
            height = image_size.height()
        else:
            pixmap = QPixmap(path)

            if pixmap.isNull():
                width = 400
                height = 300
            else:
                width = pixmap.width()
                height = pixmap.height()

        width = max(1, width)
        height = max(1, height)

        return cls(
            name=name or "Imagen",
            x=0,
            y=0,
            width=width,
            height=height,
            path=path,
        )