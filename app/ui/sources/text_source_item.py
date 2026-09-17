from __future__ import annotations

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QGraphicsTextItem

from app.sources.text_source import TextSource
from app.ui.sources.source_item import SourceItem


class TextSourceItem(SourceItem):

    @classmethod
    def create(
        cls,
        text: str = "Nuevo texto",
        name: str | None = None,
    ) -> TextSource:

        return TextSource.create(text)

    def __init__(
        self,
        source: TextSource,
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

        self.text_item = QGraphicsTextItem(
            self
        )

        self.update_visual()

    def update_visual(self) -> None:

        self.text_item.setPlainText(
            self.source.text
        )

        font = QFont()

        font.setPointSize(
            self.source.font_size
        )

        font.setBold(True)

        self.text_item.setFont(
            font
        )

        self.text_item.setDefaultTextColor(
            QColor(
                self.source.color
            )
        )

        self.text_item.setTextWidth(
            self.source.width
            * self.scale
        )

        self.text_item.setPos(
            0,
            0,
        )