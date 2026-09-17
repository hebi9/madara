from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QFont, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
)


class WorkspaceItem(QGraphicsRectItem):

    def __init__(
        self,
        workspace,
        width: float,
        height: float,
        parent=None,
    ) -> None:

        super().__init__(
            0,
            0,
            width,
            height,
            parent,
        )

        self.workspace = workspace

        self.setBrush(
            QBrush(Qt.GlobalColor.white)
        )

        self.setPen(
            QPen(
                Qt.GlobalColor.black,
                2,
            )
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            False,
        )

        self._create_label()

    def _label_text(self) -> str:

        monitor = (
            self.workspace.monitor_name
            or "Sin monitor"
        )

        return (
            f"{self.workspace.name}\n"
            f"{self.workspace.width} × {self.workspace.height}\n"
            f"{monitor}"
        )

    def _create_label(self) -> None:

        self.label = QGraphicsSimpleTextItem(
            self._label_text(),
            self,
        )

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

        self.label.setText(
            self._label_text()
        )

        self._center_label()
