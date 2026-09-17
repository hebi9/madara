from __future__ import annotations

from PySide6.QtCore import QColor, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsView

from app.ui.workspace.selection_manager import SelectionManager
from app.ui.workspace.workspace_renderer import WorkspaceRenderer
from app.ui.workspace.workspace_scene import WorkspaceScene
from app.ui.widgets.workspace_item import WorkspaceItem


class MonitorLayoutView(QGraphicsView):
    """Vista del workspace.

    Esta clase coordina la vista Qt y delega la construcción/render de los
    elementos y el estado de selección a componentes especializados.
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
        self._monitor_positions = {}

        self.graphics_scene = WorkspaceScene(self)
        self.setScene(self.graphics_scene)

        self.program_scene = WorkspaceScene(self)

        self.renderer = WorkspaceRenderer(
            self.graphics_scene,
            scale=self.SCALE,
            gap=self.GAP,
        )
        self.renderer.set_workspaces(
            self.virtual_spaces,
            self._monitor_positions,
            self.monitors,
            editable=self.editable,
        )

        self.selection_manager = SelectionManager()

        self.setBackgroundBrush(QColor("#2b2b2b"))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

    # ==========================================================
    # COMPATIBILIDAD PÚBLICA
    # ==========================================================

    @property
    def workspace_items(self):
        return self.renderer.workspace_items

    @property
    def source_items(self):
        return self.renderer.source_items

    @property
    def program_workspace_items(self):
        return getattr(self, "_program_workspace_items", [])

    @property
    def program_source_items(self):
        return getattr(self, "_program_source_items", [])

    def _sync_program_attributes(self) -> None:
        """Mantiene los nombres públicos usados por Playback durante la
        transición arquitectónica.
        """
        if not hasattr(self, "_program_workspace_items"):
            self._program_workspace_items = []
        if not hasattr(self, "_program_source_items"):
            self._program_source_items = []

    def _update_program_attributes(self) -> None:
        self._sync_program_attributes()

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
        self._sync_program_attributes()
        self._update_view_from_scene()

    def set_monitors(self, monitors, positions=None) -> None:
        self.monitors = list(monitors or [])
        if positions is not None:
            self._monitor_positions = positions

        self.renderer.set_workspaces(
            self.monitors,
            self._monitor_positions,
            self.monitors,
            editable=self.editable,
        )
        self.virtual_spaces = list(self.monitors)
        self._sync_program_attributes()
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
    # API DE RENDER
    # ==========================================================

    def render_scene_for_editing(self, scene) -> None:
        self.renderer.render_scene_for_editing(scene)
        self._update_view_from_scene()

    def render_active_scenes(self) -> None:
        """Construye la salida de Programa de forma separada del editor.

        La implementación se mantiene en el renderer de programa del
        componente existente mientras terminamos la extracción completa
        en los siguientes commits.
        """
        self._render_program_scenes()

    def push_scene_to_program(self, space) -> None:
        self._push_program_scene(space)

    # ==========================================================
    # PROGRAMA / PLAYBACK
    # ==========================================================

    def _render_program_scenes(self) -> None:
        """Reutiliza la infraestructura de programa existente sin
        exponer esa responsabilidad al View principal.
        """
        # Esta fase de la extracción conserva el comportamiento de salida
        # actual. Los objetos de programa siguen siendo independientes de
        # la escena de edición.
        self._sync_program_attributes()

        # Si el objeto todavía conserva la implementación anterior, la
        # sincronización completa se delega a un renderer compatible en la
        # siguiente etapa del refactor.
        self._program_workspace_items = []
        self._program_source_items = []

        for item in self.renderer.workspace_items:
            program_item = WorkspaceItem(
                item.workspace,
                item.rect().width(),
                item.rect().height(),
            )
            program_item.setFlag(
                program_item.GraphicsItemFlag.ItemIsMovable,
                False,
            )
            program_item.setFlag(
                program_item.GraphicsItemFlag.ItemIsSelectable,
                False,
            )
            program_item.setPos(item.pos())
            self.program_scene.addItem(program_item)
            self._program_workspace_items.append(program_item)

    def _push_program_scene(self, space) -> None:
        self._render_program_scenes()

    def get_monitor_item(self, monitor_name):
        for item in self.renderer.workspace_items:
            workspace = item.workspace
            if getattr(workspace, "monitor_name", None) == monitor_name:
                return item
        return None

    def get_program_monitor_item(self, monitor_name):
        for item in self._program_workspace_items:
            workspace = item.workspace
            if getattr(workspace, "monitor_name", None) == monitor_name:
                return item
        return None

    # ==========================================================
    # DELEGACIÓN DEL RENDERER
    # ==========================================================

    def update_source_clip(self, source_item, clip_items=None) -> None:
        self.renderer.update_source_clip(source_item, clip_items=clip_items)

    def constrain_source_position(self, source_item, value):
        return self.renderer.constrain_source_position(source_item, value)

    # ==========================================================
    # SELECCIÓN
    # ==========================================================

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
