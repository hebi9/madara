from __future__ import annotations

from PySide6.QtCore import QColor, QPointF, Qt
from PySide6.QtWidgets import QGraphicsView

from app.ui.workspace.selection_manager import SelectionManager
from app.ui.workspace.workspace_renderer import WorkspaceRenderer
from app.ui.workspace.workspace_scene import WorkspaceScene
from app.ui.widgets.workspace_item import WorkspaceItem


class MonitorLayoutView(QGraphicsView):
    """Vista del workspace.

    La vista coordina Qt y delega construcción/render y selección a
    componentes especializados. La escena de Programa se mantiene
    separada del editor para preservar la independencia del reproductor.
    """

    SCALE = 0.15
    GAP = 60

    def __init__(
        self,
        workspaces=None,
        editable=False,
        monitors=None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.editable = editable
        self.virtual_spaces = list(workspaces or [])
        self.monitors = list(monitors or [])
        self._monitor_positions: dict[str, QPointF] = {}

        self.graphics_scene = WorkspaceScene(self)
        self.setScene(self.graphics_scene)

        # La escena de Programa nunca comparte QGraphicsItem con el editor.
        self.program_scene = WorkspaceScene(self)
        self._program_workspace_items = []
        self._program_source_items = []

        self.renderer = WorkspaceRenderer(
            self.graphics_scene,
            scale=self.SCALE,
            gap=self.GAP,
        )
        self.selection_manager = SelectionManager()

        self.setBackgroundBrush(QColor("#2b2b2b"))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

        self.set_workspaces(
            self.virtual_spaces,
            self._monitor_positions,
            self.monitors,
        )

    # ==========================================================
    # PROPIEDADES DE COMPATIBILIDAD
    # ==========================================================

    @property
    def workspace_items(self):
        return self.renderer.workspace_items

    @property
    def source_items(self):
        return self.renderer.source_items

    @property
    def program_workspace_items(self):
        return self._program_workspace_items

    @property
    def program_source_items(self):
        return self._program_source_items

    @property
    def monitor_items(self):
        # Compatibilidad con código existente. El modelo canónico del
        # editor son los espacios virtuales, no los monitores físicos.
        return self.renderer.workspace_items

    # ==========================================================
    # CONFIGURACIÓN
    # ==========================================================

    def set_workspaces(
        self,
        workspaces,
        monitor_positions=None,
        monitors=None,
    ) -> None:
        self.virtual_spaces = list(workspaces or [])
        self._monitor_positions = monitor_positions or {}
        self.monitors = list(monitors or [])

        self.renderer.set_workspaces(
            self.virtual_spaces,
            self._monitor_positions,
            self.monitors,
            editable=self.editable,
        )
        self._update_view_from_scene()

    def set_monitors(self, monitors, positions=None) -> None:
        """Configura la vista usada por SettingsDialog.

        Settings trabaja con MonitorInfo, mientras que el editor trabaja
        con VirtualSpace. WorkspaceRenderer adapta ambos formatos sin
        guardar monitores físicos dentro del modelo de proyecto.
        """
        self.monitors = list(monitors or [])
        if positions is not None:
            self._monitor_positions = positions

        self.renderer.set_workspaces(
            self.monitors,
            self._monitor_positions,
            self.monitors,
            editable=True,
        )
        self._update_view_from_scene()

    def set_monitor_positions(self, positions) -> None:
        self._monitor_positions = positions or {}
        self.renderer.set_workspaces(
            self.virtual_spaces,
            self._monitor_positions,
            self.monitors,
            editable=self.editable,
        )
        self._update_view_from_scene()

    def monitor_positions(self):
        return self.renderer.monitor_positions_snapshot()

    # ==========================================================
    # EDITOR
    # ==========================================================

    def render_scene_for_editing(self, scene) -> None:
        self.renderer.render_scene_for_editing(scene)
        self._update_view_from_scene()

    # ==========================================================
    # PROGRAMA / PLAYBACK
    # ==========================================================

    def render_active_scenes(self) -> None:
        """Reconstruye los elementos de programa de forma aislada.

        La fuente de datos sigue siendo la escena activa de cada espacio.
        El render del editor no comparte QGraphicsItem con esta escena.
        """
        self._clear_program_items()

        for workspace_item in self.renderer.workspace_items:
            workspace = workspace_item.workspace
            scene = getattr(workspace, "active_scene", None)
            if scene is None:
                continue

            self._create_program_workspace_item(workspace_item)

        # Segundo paso: crear las fuentes sobre los espacios ya creados.
        for program_workspace_item in self._program_workspace_items:
            workspace = program_workspace_item.workspace
            scene = getattr(workspace, "active_scene", None)
            if scene is None:
                continue

            for source_definition in scene.sources:
                item = self.renderer.create_source_item(source_definition)
                if item is None:
                    continue

                item.setPos(
                    program_workspace_item.x()
                    + source_definition.x * self.SCALE,
                    program_workspace_item.y()
                    + source_definition.y * self.SCALE,
                )
                item.set_editable(False)
                item.owner_space = workspace
                self.program_scene.addItem(item)
                self._program_source_items.append(item)

                self.renderer.update_source_clip(
                    item,
                    clip_items=self._program_workspace_items,
                )

        self._update_program_scene_rect()

    def push_scene_to_program(self, space) -> None:
        """Actualiza explícitamente Programa sin tocar el editor."""
        self.render_active_scenes()

    def _create_program_workspace_item(self, editor_item) -> None:
        item = WorkspaceItem(
            editor_item.workspace,
            editor_item.rect().width(),
            editor_item.rect().height(),
        )
        item.setFlag(
            item.GraphicsItemFlag.ItemIsMovable,
            False,
        )
        item.setFlag(
            item.GraphicsItemFlag.ItemIsSelectable,
            False,
        )
        item.setPos(editor_item.pos())
        self.program_scene.addItem(item)
        self._program_workspace_items.append(item)

    def _clear_program_items(self) -> None:
        for item in self._program_source_items:
            dispose = getattr(item, "dispose", None)
            if dispose is not None:
                dispose()
            if item.scene() is not None:
                self.program_scene.removeItem(item)

        self._program_source_items.clear()

        for item in self._program_workspace_items:
            if item.scene() is not None:
                self.program_scene.removeItem(item)

        self._program_workspace_items.clear()

        # QGraphicsScene.clear() también elimina cualquier elemento
        # residual creado durante una transición anterior.
        self.program_scene.clear()

    def _update_program_scene_rect(self) -> None:
        if not self._program_workspace_items:
            self.program_scene.setSceneRect(0, 0, 100, 100)
            return

        from PySide6.QtCore import QRectF

        rect = QRectF()
        for item in self._program_workspace_items:
            rect = rect.united(item.sceneBoundingRect())
        self.program_scene.setSceneRect(rect)

    def get_monitor_item(self, monitor_name):
        return self.renderer.get_workspace_item_for_monitor(monitor_name)

    def get_program_monitor_item(self, monitor_name):
        for item in self._program_workspace_items:
            workspace = item.workspace
            if getattr(workspace, "monitor_name", None) == monitor_name:
                return item
            if getattr(workspace, "name", None) == monitor_name:
                return item
        return None

    # ==========================================================
    # DELEGACIÓN
    # ==========================================================

    def update_source_clip(self, source_item, clip_items=None) -> None:
        self.renderer.update_source_clip(
            source_item,
            clip_items=clip_items,
        )

    def constrain_source_position(self, source_item, value):
        return self.renderer.constrain_source_position(
            source_item,
            value,
        )

    def get_selected_source(self):
        return self.renderer.get_selected_source()

    def get_selected_workspace(self):
        return self.renderer.get_selected_workspace()

    def get_workspace_from_item(self, item):
        return self.renderer.get_workspace_from_item(item)

    # ==========================================================
    # VISTA
    # ==========================================================

    def _update_view_from_scene(self) -> None:
        rect = self.graphics_scene.sceneRect()
        if rect.isNull() or rect.isEmpty():
            return

        self.fitInView(
            rect,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_view_from_scene()
