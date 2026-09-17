from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGraphicsScene


class WorkspaceScene(QGraphicsScene):
    """Escena gráfica dedicada al editor de espacios virtuales.

    La clase contiene únicamente la responsabilidad propia de una
    QGraphicsScene y expone señales semánticas para que la UI pueda
    reaccionar a la selección sin acoplarse a los detalles de Qt.
    """

    workspace_selected = Signal(object)
    source_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def selected_workspace_item(self):
        for item in self.selectedItems():
            if hasattr(item, "workspace"):
                return item
        return None

    def selected_source_item(self):
        for item in self.selectedItems():
            if hasattr(item, "source"):
                return item
        return None
