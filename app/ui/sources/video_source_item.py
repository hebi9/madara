from __future__ import annotations

import logging

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink
from PySide6.QtWidgets import QGraphicsPixmapItem

from app.sources.video_source import VideoSource
from app.ui.sources.source_item import SourceItem


logger = logging.getLogger(__name__)


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
        self.video_sink = QVideoSink()
        self.video_sink.videoFrameChanged.connect(self._video_frame_changed)
        self.pixmap_item = QGraphicsPixmapItem(self)
        self.pixmap_item.setTransformationMode(
            Qt.TransformationMode.SmoothTransformation
        )
        self.player = QMediaPlayer()
        self.player.setVideoSink(self.video_sink)
        # El editor previsualiza el video en silencio; el Programa también emite audio.
        self._audible = workspace_view is None
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0 if self._audible else 0.0)
        self.audio_output.setMuted(not self._audible)
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(source.path))
        self.player.mediaStatusChanged.connect(self._media_status_changed)
        self.player.errorOccurred.connect(self._playback_error)
        self._start_when_loaded = False

    def _media_status_changed(self, status) -> None:
        if (
            status
            in (
                QMediaPlayer.MediaStatus.LoadedMedia,
                QMediaPlayer.MediaStatus.BufferedMedia,
            )
            and self._start_when_loaded
        ):
            self._start_when_loaded = False
            self.player.setPosition(0)
            self.player.play()

        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()

    def _video_frame_changed(self, frame) -> None:
        if not frame.isValid():
            return
        image = frame.toImage()
        if image.isNull():
            return
        self.pixmap_item.setPixmap(QPixmap.fromImage(image))
        self.update_visual()

    def start_preview(self) -> None:
        self.audio_output.setVolume(0.0)
        self.audio_output.setMuted(True)
        self._start_from_zero_when_ready()

    def start_from_zero(self) -> None:
        self.audio_output.setVolume(1.0)
        self.audio_output.setMuted(False)
        self._start_from_zero_when_ready()

    def _start_from_zero_when_ready(self) -> None:
        if self.player.mediaStatus() in (
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
        ):
            self._start_when_loaded = False
            self.player.setPosition(0)
            self.player.play()
            return

        self._start_when_loaded = True

    def stop_playback(self) -> None:
        self._start_when_loaded = False
        self.audio_output.setMuted(True)
        self.player.stop()

    def _playback_error(self, error, error_string) -> None:
        logger.error(
            "No se pudo reproducir el video %s (Qt %s): %s",
            self.source.path,
            error,
            error_string,
        )
        self._last_error = error_string

    def update_visual(self) -> None:
        pixmap = self.pixmap_item.pixmap()
        if pixmap.isNull():
            return

        target_width = max(1.0, self.rect().width())
        target_height = max(1.0, self.rect().height())
        image_scale = min(
            target_width / pixmap.width(),
            target_height / pixmap.height(),
        )
        rendered_width = pixmap.width() * image_scale
        rendered_height = pixmap.height() * image_scale

        self.pixmap_item.setTransform(
            QTransform.fromScale(image_scale, image_scale)
        )
        self.pixmap_item.setPos(
            (target_width - rendered_width) / 2,
            (target_height - rendered_height) / 2,
        )

    def set_audio_output(self, device) -> None:
        self.audio_output.setDevice(device)

    def dispose(self) -> None:
        self.stop_playback()
        self.audio_output.deleteLater()
        self.player.deleteLater()
