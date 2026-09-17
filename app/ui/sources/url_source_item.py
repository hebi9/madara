from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QGraphicsProxyWidget

from app.sources.url_source import UrlSource
from app.ui.sources.source_item import SourceItem


class UrlSourceItem(SourceItem):
    def __init__(
        self,
        source: UrlSource,
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
        self.web_view = QWebEngineView()
        self.web_view.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.web_view.setUrl(source.web_url())
        self.proxy = QGraphicsProxyWidget(self)
        self.proxy.setWidget(self.web_view)
        self.update_visual()

    def update_visual(self) -> None:
        self.web_view.resize(
            max(1, round(self.rect().width())),
            max(1, round(self.rect().height())),
        )

    def dispose(self) -> None:
        self.web_view.stop()
        self.web_view.deleteLater()
