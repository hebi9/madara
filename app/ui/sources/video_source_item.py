from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
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
        self.audio_output = QAudioOutput()
        # El editor puede mostrar el video sin duplicar el audio del programa.
        self.audio_output.setVolume(0.0 if workspace_view is not None else 1.0)
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(source.path))
        self.player.mediaStatusChanged.connect(self._media_status_changed)
        self._started_from_zero = False
        self.update_visual()
        self.player.setPosition(0)
        self.player.play()

    def _media_status_changed(self, status) -> None:
        if (
            status == QMediaPlayer.MediaStatus.LoadedMedia
            and not self._started_from_zero
        ):
            self._started_from_zero = True
            self.player.setPosition(0)
            self.player.play()

        if self.source.loop and status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    def update_visual(self) -> None:
        self.video_item.setSize(self.rect().size())

    def set_audio_output(self, device) -> None:
        self.audio_output.setDevice(device)

    def dispose(self) -> None:
        self.player.stop()
        self.audio_output.deleteLater()
        self.player.deleteLater()
