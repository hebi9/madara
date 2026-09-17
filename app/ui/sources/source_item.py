from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsRectItem


class SourceItem(QGraphicsRectItem):
    HANDLE_SIZE = 8

    def __init__(
        self,
        source,
        scale: float,
        canvas_width: float,
        canvas_height: float,
        parent=None,
        owner_canvas=None,
        bounds_rect=None,
        workspace_view=None,
    ) -> None:
        self.source = source
        self.scale = scale
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.owner_canvas = owner_canvas
        self.bounds_rect = bounds_rect
        self.workspace_view = workspace_view
        self.source_definition = None
        self.workspace_item = None
        self._clip_path = QPainterPath()
        self.active_handle = None
        self._drag_start_pos = QPointF()

        super().__init__(0, 0, source.width * scale, source.height * scale, parent)
        self.set_editable(False)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setPen(QPen(Qt.GlobalColor.transparent))

    def boundingRect(self) -> QRectF:
        margin = self.HANDLE_SIZE
        return self.rect().adjusted(-margin, -margin, margin, margin)

    def set_editable(self, editable: bool) -> None:
        self.setFlag(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable,
            bool(editable) and not self.source.locked,
        )

    def shape(self) -> QPainterPath:
        # El clipping es solo visual. No lo usamos como shape de selección,
        # porque entonces una fuente fuera del EV deja de poder seleccionarse
        # o arrastrarse y los handles desaparecen en los bordes.
        return super().shape()

    def update_clip(self) -> None:
        self._clip_path = QPainterPath()
        if self.workspace_view is not None:
            self.workspace_view.update_source_clip(self)

    def _clamp_position(self, value: QPointF) -> QPointF:
        return value

    def handles(self):
        r = self.rect()
        s = self.HANDLE_SIZE
        return {
            "tl": QRectF(r.left() - s / 2, r.top() - s / 2, s, s),
            "tr": QRectF(r.right() - s / 2, r.top() - s / 2, s, s),
            "bl": QRectF(r.left() - s / 2, r.bottom() - s / 2, s, s),
            "br": QRectF(r.right() - s / 2, r.bottom() - s / 2, s, s),
        }

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if not self.isSelected():
            return
        painter.save()
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        for rect in self.handles().values():
            painter.drawRect(rect)
        painter.restore()

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            if self.workspace_view is not None:
                value = self.workspace_view.constrain_source_position(self, value)
            return super().itemChange(change, value)

        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            self.source.x = self.x() / self.scale
            self.source.y = self.y() / self.scale
            if self.source_definition is not None and self.source_definition is not self.source:
                self.source_definition.x = round(self.source.x)
                self.source_definition.y = round(self.source.y)
            if self.workspace_view is not None:
                self.workspace_view.update_source_clip(self)

        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.active_handle = None
        if self.isSelected():
            for name, rect in self.handles().items():
                if rect.contains(event.pos()):
                    self.active_handle = name
                    self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape, False)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.active_handle is None:
            super().mouseMoveEvent(event)
            return

        r = self.rect()
        p = event.pos()
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        if self.active_handle == "br":
            w, h = max(10, p.x()), max(10, p.y())
        elif self.active_handle == "tr":
            h = max(10, r.bottom() - p.y())
            y = r.bottom() - h
            w = max(10, p.x())
        elif self.active_handle == "bl":
            w = max(10, r.right() - p.x())
            x = r.right() - w
            h = max(10, p.y())
        elif self.active_handle == "tl":
            w = max(10, r.right() - p.x())
            h = max(10, r.bottom() - p.y())
            x = r.right() - w
            y = r.bottom() - h

        self.prepareGeometryChange()
        self.setRect(x, y, w, h)
        self.source.width = w / self.scale
        self.source.height = h / self.scale
        if self.source_definition is not None and self.source_definition is not self.source:
            self.source_definition.width = round(self.source.width)
            self.source_definition.height = round(self.source.height)
        self.update_visual()
        if self.workspace_view is not None:
            self.workspace_view.update_source_clip(self)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.active_handle = None
        self.setFlag(self.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        if self.workspace_view is not None:
            self.workspace_view.update_source_clip(self)
        super().mouseReleaseEvent(event)

    def set_source_position(self, x: float, y: float) -> None:
        self.source.x = x
        self.source.y = y
        if self.source_definition is not None and self.source_definition is not self.source:
            self.source_definition.x = round(x)
            self.source_definition.y = round(y)
        self.setPos(x * self.scale, y * self.scale)

    def set_source_size(self, width: float, height: float) -> None:
        width = max(1.0, width)
        height = max(1.0, height)
        self.source.width = width
        self.source.height = height
        if self.source_definition is not None and self.source_definition is not self.source:
            self.source_definition.width = round(width)
            self.source_definition.height = round(height)
        self.prepareGeometryChange()
        self.setRect(0, 0, width * self.scale, height * self.scale)
        self.update_visual()
        if self.workspace_view is not None:
            self.workspace_view.update_source_clip(self)

    def update_visual(self) -> None:
        pass
