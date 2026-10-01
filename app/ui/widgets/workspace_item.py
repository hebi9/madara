from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QFont, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsSimpleTextItem


class WorkspaceItem(QGraphicsRectItem):
    """Representación gráfica de un VirtualSpace o monitor físico temporal."""

    def __init__(self, workspace, width: float, height: float, parent=None) -> None:
        super().__init__(0, 0, width, height, parent)
        self.workspace = workspace
        self.position_changed_callback = None
        self.setBrush(QBrush(Qt.GlobalColor.white))
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self._create_label()

    def itemChange(self, change, value):
        result = super().itemChange(change, value)

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if hasattr(self.workspace, "x") and hasattr(self.workspace, "y"):
                self.workspace.x = float(value.x())
                self.workspace.y = float(value.y())

            callback = self.position_changed_callback
            if callback is not None:
                callback()

        return result

    def _label_text(self) -> str:
        monitor = getattr(self.workspace, "monitor_name", None) or "Sin monitor"
        name = getattr(self.workspace, "name", "Monitor")
        width = getattr(self.workspace, "width", self.rect().width())
        height = getattr(self.workspace, "height", self.rect().height())
        return f"{name}\n{int(width)} × {int(height)}\n{monitor}"

    def _create_label(self) -> None:
        self.label = QGraphicsSimpleTextItem(self._label_text(), self)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresParentOpacity,
            True,
        )
        self._center_label()

    def _center_label(self) -> None:
        rect = self.label.boundingRect()
        self.label.setPos(
            (self.rect().width() - rect.width()) / 2,
            self.rect().height() + 10,
        )

    def refresh_label(self) -> None:
        self.label.setText(self._label_text())
        self._center_label()
