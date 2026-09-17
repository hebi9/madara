from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem

from app.sources.video_source import VideoSource
from app.ui.sources.source_item import SourceItem


class VideoSourceItem(SourceItem):
    def __init__(
        self,
        source: VideoSource,
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
        self.video_item = QGraphicsVideoItem(self)
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_item)
        self.player.setSource(QUrl.fromLocalFile(source.path))
        self.player.mediaStatusChanged.connect(self._media_status_changed)
        self.update_visual()
        self.player.play()

    def _media_status_changed(self, status) -> None:
        if self.source.loop and status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    def update_visual(self) -> None:
        self.video_item.setSize(self.rect().size())

    def dispose(self) -> None:
        self.player.stop()
        self.player.deleteLater()
