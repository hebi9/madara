from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTransform
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

        target_width = max(1.0, float(self.source.width * self.scale))
        target_height = max(1.0, float(self.source.height * self.scale))

        # Conservamos el pixmap original a su resolución completa.
        # No generamos una copia pequeña para el editor: esa copia después
        # tendría que ampliarse en playback y produciría pixelación.
        scale_x = target_width / max(1, self.pixmap.width())
        scale_y = target_height / max(1, self.pixmap.height())
        image_scale = min(scale_x, scale_y)

        rendered_width = self.pixmap.width() * image_scale
        rendered_height = self.pixmap.height() * image_scale

        self.pixmap_item.setPixmap(self.pixmap)
        self.pixmap_item.setTransform(
            QTransform.fromScale(image_scale, image_scale)
        )
        self.pixmap_item.setPos(
            (target_width - rendered_width) / 2,
            (target_height - rendered_height) / 2,
        )
                target_width
                - scaled.width()
            ) / 2,
            (
                target_height
                - scaled.height()
            ) / 2,
        )