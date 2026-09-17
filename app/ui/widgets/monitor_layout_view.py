from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsView

from app.ui.workspace.selection_manager import SelectionManager
from app.ui.workspace.workspace_renderer import WorkspaceRenderer
from app.ui.workspace.workspace_scene import WorkspaceScene
from app.ui.widgets.workspace_item import WorkspaceItem


class MonitorLayoutView(QGraphicsView):
    """Vista gráfica del workspace.

    La vista se ocupa de presentar la escena y delega la construcción de
    elementos al renderer. La escena de Programa permanece separada del
    editor.
    """

    SCALE = 0.15
    GAP = 60

    def __init__(self, workspaces=None, editable=False, monitors=None, parent=None) -> None:
        super().__init__(parent)
        self.editable = editable
        self.virtual_spaces = list(workspaces or [])
        self.monitors = list(monitors or [])
        self._monitor_positions: dict[str, QPointF] = {}
        self.graphics_scene = WorkspaceScene(self)
        self.setScene(self.graphics_scene)
        self.program_scene = WorkspaceScene(self)
        self._program_workspace_items = []
        self._program_source_items = []
        self.renderer = WorkspaceRenderer(self.graphics_scene, scale=self.SCALE, gap=self.GAP)
        self.selection_manager = SelectionManager()
        self.setBackgroundBrush(QColor('#2b2b2b'))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.set_workspaces(self.virtual_spaces, self._monitor_positions, self.monitors)

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
        return self.renderer.workspace_items

    def set_workspaces(self, workspaces, monitor_positions=None, monitors=None):
        self.virtual_spaces = list(workspaces or [])
        self._monitor_positions = monitor_positions or {}
        self.monitors = list(monitors or [])
        self.renderer.set_workspaces(self.virtual_spaces, self._monitor_positions, self.monitors, editable=self.editable)
        self._rebuild_program_workspaces(); self._update_view_from_scene()

    def set_monitors(self, monitors, positions=None):
        self.monitors = list(monitors or [])
        if positions is not None: self._monitor_positions = positions
        self._clear_program_items(); x = 0.0
        for monitor in self.monitors:
            width = monitor.geometry.width() * self.SCALE; height = monitor.geometry.height() * self.SCALE
            class _MonitorLayoutAdapter: pass
            adapter = _MonitorLayoutAdapter(); adapter.name = monitor.name; adapter.width = monitor.geometry.width(); adapter.height = monitor.geometry.height(); adapter.monitor_name = monitor.name
            item = WorkspaceItem(adapter, width, height); item.setFlag(item.GraphicsItemFlag.ItemIsMovable, self.editable)
            position = self._monitor_positions.get(monitor.name); item.setPos(position if position is not None else QPointF(x, 0)); self.program_scene.addItem(item); self._program_workspace_items.append(item); x += width + self.GAP
        self._update_program_scene_rect()

    def set_monitor_positions(self, positions):
        self._monitor_positions = positions or {}
        if self.monitors and not self.virtual_spaces: self.set_monitors(self.monitors, self._monitor_positions); return
        self.renderer.set_workspaces(self.virtual_spaces, self._monitor_positions, self.monitors, editable=self.editable); self._rebuild_program_workspaces(); self._update_view_from_scene()

    def monitor_positions(self):
        if self.monitors and not self.virtual_spaces:
            return {item.workspace.monitor_name: item.pos() for item in self._program_workspace_items if getattr(item.workspace, 'monitor_name', None)}
        return self.renderer.monitor_positions_snapshot()

    def render_scene_for_editing(self, scene): self.renderer.render_scene_for_editing(scene); self._update_view_from_scene()

    def render_active_scenes(self): self._rebuild_program_workspaces();
        
        for program_workspace_item in self._program_workspace_items:
            scene = getattr(program_workspace_item.workspace, 'active_scene', None)
            if scene is None: continue
            for source_definition in scene.sources:
                item = self.renderer.create_source_item(source_definition)
                if item is None: continue
                item.setPos(program_workspace_item.x() + source_definition.x * self.SCALE, program_workspace_item.y() + source_definition.y * self.SCALE); item.set_editable(False); item.owner_space = program_workspace_item.workspace; self.program_scene.addItem(item); self._program_source_items.append(item); self.renderer.update_source_clip(item, clip_items=self._program_workspace_items)
        self._update_program_scene_rect()

    def push_scene_to_program(self, space): self.render_active_scenes()

    def _rebuild_program_workspaces(self):
        self._clear_program_items();
        
        for workspace_item in self.renderer.workspace_items:
            item = WorkspaceItem(workspace_item.workspace, workspace_item.rect().width(), workspace_item.rect().height()); item.setFlag(item.GraphicsItemFlag.ItemIsMovable, False); item.setFlag(item.GraphicsItemFlag.ItemIsSelectable, False); item.setPos(workspace_item.pos()); self.program_scene.addItem(item); self._program_workspace_items.append(item)
        self._update_program_scene_rect()

    def _clear_program_items(self):
        for item in self._program_source_items:
            dispose = getattr(item, 'dispose', None)
            if dispose is not None: dispose()
            if item.scene() is not None: self.program_scene.removeItem(item)
        self._program_source_items.clear();
        
        for item in self._program_workspace_items:
            if item.scene() is not None: self.program_scene.removeItem(item)
        self._program_workspace_items.clear(); self.program_scene.clear()

    def _update_program_scene_rect(self):
        from PySide6.QtCore import QRectF
        if not self._program_workspace_items: self.program_scene.setSceneRect(0, 0, 100, 100); return
        rect = QRectF();
        
        for item in self._program_workspace_items: rect = rect.united(item.sceneBoundingRect())
        self.program_scene.setSceneRect(rect)

    def get_monitor_item(self, monitor_name): return self.renderer.get_workspace_item_for_monitor(monitor_name)

    def get_program_monitor_item(self, monitor_name):
        for item in self._program_workspace_items:
            workspace = item.workspace
            if getattr(workspace, 'monitor_name', None) == monitor_name or getattr(workspace, 'name', None) == monitor_name: return item
        return None

    def update_source_clip(self, source_item, clip_items=None): self.renderer.update_source_clip(source_item, clip_items=clip_items)
    def constrain_source_position(self, source_item, value): return self.renderer.constrain_source_position(source_item, value)
    def get_selected_source(self): return self.renderer.get_selected_source()
    def get_selected_workspace(self): return self.renderer.get_selected_workspace()
    def get_workspace_from_item(self, item): return self.renderer.get_workspace_from_item(item)

    def _update_view_from_scene(self):
        rect = self.graphics_scene.sceneRect();
        if not rect.isNull() and not rect.isEmpty(): self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event): super().resizeEvent(event); self._update_view_from_scene()