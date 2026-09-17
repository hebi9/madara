from __future__ import annotations


class SelectionManager:
    """Mantiene el estado de selección lógica del editor.

    La selección de datos se mantiene separada de los QGraphicsItem.
    El manager no conoce Qt ni modifica directamente la escena gráfica.
    """

    def __init__(self) -> None:
        self.selected_space = None
        self.selected_scene = None
        self.selected_source = None

    def select_space(self, space) -> None:
        self.selected_space = space
        self.selected_scene = None
        self.selected_source = None

    def select_scene(self, scene) -> None:
        self.selected_scene = scene
        self.selected_source = None

    def select_source(self, source) -> None:
        self.selected_source = source

    def clear_source(self) -> None:
        self.selected_source = None

    def clear(self) -> None:
        self.selected_space = None
        self.selected_scene = None
        self.selected_source = None
