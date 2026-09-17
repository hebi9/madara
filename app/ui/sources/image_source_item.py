from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem

from app.sources.image_source import ImageSource
from app.ui.sources.source_item import SourceItem


class ImageSourceItem(SourceItem):

    @classmethod
    def create(
        cls,
        path: str,
        name: str | None = None,
    ) -> ImageSource:

        return ImageSource.create(
            path,
            name=name,
        )

    def __init__(
        self,
        source: ImageSource,
        scale: float,
        canvas_width: float,
        canvas_height: float,
        parent=None,
        owner_canvas=None,
        bounds_rect=None,
        workspace_view=None,
    ) -> None:

        super().__init__(
            source=source,
            scale=scale,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            parent=parent,
            owner_canvas=owner_canvas,
            bounds_rect=bounds_rect,
            workspace_view=workspace_view,
        )

        self.pixmap_item = QGraphicsPixmapItem(
            self
        )

        self.pixmap = QPixmap(
            source.path
        )

        self.update_visual()

    def update_visual(self) -> None:

        if self.pixmap.isNull():
            return

        target_width = max(
            1,
            int(
                self.source.width
                * self.scale
            ),
        )

        target_height = max(
            1,
            int(
                self.source.height
                * self.scale
            ),
        )

        scaled = self.pixmap.scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.pixmap_item.setPixmap(
            scaled
        )

        self.pixmap_item.setPos(
            (
                target_width
                - scaled.width()
            ) / 2,
            (
                target_height
                - scaled.height()
            ) / 2,
        )