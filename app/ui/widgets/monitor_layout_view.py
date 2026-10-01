from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsView

from app.ui.workspace.selection_manager import SelectionManager
from app.ui.workspace.workspace_renderer import WorkspaceRenderer
from app.ui.workspace.workspace_scene import WorkspaceScene
from app.ui.widgets.workspace_item import WorkspaceItem


class MonitorLayoutView(QGraphicsView):
    """Editor lógico y layout físico de monitores."""

    SCALE = 0.15
    GAP = 60

    def __init__(self, workspaces=None, editable=False, monitors=None, parent=None) -> None:
        super().__init__(parent)

        self.editable = editable
        self.virtual_spaces = []
        self.monitors = list(monitors or [])
        self._monitor_positions: dict[str, QPointF] = {}

        self.graphics_scene = WorkspaceScene(self)
        self.program_scene = WorkspaceScene(self)

        self._program_workspace_items: list[WorkspaceItem] = []
        self._program_source_items = []
        self._program_snapshot = None

        self._settings_scene = None
        self._settings_workspace_items: list[WorkspaceItem] = []
        self._settings_mode = False

        self.setScene(self.graphics_scene)

        self.renderer = WorkspaceRenderer(
            self.graphics_scene,
            scale=self.SCALE,
            gap=self.GAP,
        )

        self.selection_manager = SelectionManager()

        self.setBackgroundBrush(QColor("#2b2b2b"))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

        if workspaces:
            first = workspaces[0]
            if hasattr(first, "geometry"):
                self.set_monitors(workspaces, self._monitor_positions)
            else:
                self.set_workspaces(
                    workspaces,
                    self._monitor_positions,
                    self.monitors,
                )

    @property
    def workspace_items(self):
        if self._settings_mode:
            return self._settings_workspace_items
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
        return self.workspace_items

    # ==========================================================
    # EDITOR LÓGICO
    # ==========================================================

    def set_workspaces(self, workspaces, monitor_positions=None, monitors=None) -> None:
        self._settings_mode = False
        self.setScene(self.graphics_scene)

        self.virtual_spaces = list(workspaces or [])
        self.monitors = list(monitors or [])
        self._monitor_positions = dict(monitor_positions or {})

        self.renderer.set_workspaces(
            self.virtual_spaces,
            {},
            self.monitors,
            editable=self.editable,
        )

        # La disposición física de Settings se aplica aquí únicamente como
        # posición visual del EV asignado al monitor. No modifica su tamaño,
        # ni la geometría lógica del proyecto.
        for item in self.renderer.workspace_items:
            position = self._monitor_positions.get(
                getattr(item.workspace, "monitor_name", None)
            )
            if position is not None:
                item.setPos(self._to_qpointf(position))

        self.renderer.update_scene_rect()
        self._update_view_from_scene()

    def render_scene_for_editing(self, scene) -> None:
        self._settings_mode = False
        self.setScene(self.graphics_scene)

        self.renderer.render_scene_for_editing(scene)

        # render_scene_for_editing reconstruye los WorkspaceItems; reaplicamos
        # la posición física al EV correspondiente sin tocar VirtualSpace.x/y.
        for item in self.renderer.workspace_items:
            position = self._monitor_positions.get(
                getattr(item.workspace, "monitor_name", None)
            )
            if position is not None:
                item.setPos(self._to_qpointf(position))

        self.renderer.update_scene_rect()
        self._update_view_from_scene()

    # ==========================================================
    # SETTINGS / MONITORES FÍSICOS
    # ==========================================================

    def set_monitors(self, monitors, positions=None) -> None:
        self._settings_mode = True
        self.monitors = list(monitors or [])

        if positions is not None:
            self._monitor_positions = {
                name: self._to_qpointf(position)
                for name, position in positions.items()
            }

        if self._settings_scene is None:
            self._settings_scene = WorkspaceScene(self)

        self._settings_scene.clear()
        self._settings_workspace_items.clear()

        x = 0.0
        for monitor in self.monitors:
            width = monitor.geometry.width() * self.SCALE
            height = monitor.geometry.height() * self.SCALE

            class _Monitor:
                pass

            physical = _Monitor()
            physical.name = monitor.name
            physical.width = monitor.geometry.width()
            physical.height = monitor.geometry.height()
            physical.monitor_name = monitor.name

            item = WorkspaceItem(
                physical,
                width,
                height,
            )

            item.setFlag(
                item.GraphicsItemFlag.ItemIsMovable,
                self.editable,
            )
            item.setFlag(
                item.GraphicsItemFlag.ItemIsSelectable,
                False,
            )

            position = self._monitor_positions.get(monitor.name)
            if position is None:
                position = QPointF(x, 0)
            else:
                position = self._to_qpointf(position)

            item.setPos(position)
            self._settings_scene.addItem(item)
            self._settings_workspace_items.append(item)

            x += width + self.GAP

        self.setScene(self._settings_scene)

        rect = self._settings_scene.itemsBoundingRect()
        if rect.isEmpty():
            rect = QRectF(0, 0, 100, 100)
        self._settings_scene.setSceneRect(
            rect.adjusted(-120, -120, 120, 120)
        )
        self.fitInView(
            self._settings_scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def set_monitor_positions(self, positions) -> None:
        self._monitor_positions = {
            name: self._to_qpointf(position)
            for name, position in (positions or {}).items()
        }

        if self._settings_mode:
            self.set_monitors(
                self.monitors,
                self._monitor_positions,
            )
            return

        self.set_workspaces(
            self.virtual_spaces,
            self._monitor_positions,
            self.monitors,
        )

    def monitor_positions(self):
        if self._settings_mode:
            return {
                item.workspace.monitor_name: QPointF(item.pos())
                for item in self._settings_workspace_items
                if getattr(item.workspace, "monitor_name", None)
            }

        return dict(self._monitor_positions)

    # ==========================================================
    # PROGRAM SNAPSHOT
    # ==========================================================

    def capture_program_snapshot(self) -> None:
        snapshot = []

        for workspace in self.virtual_spaces:
            scene = getattr(workspace, "active_scene", None)
            if scene is None:
                continue

            sources = [
                {
                    "source": source,
                    "x": float(source.x),
                    "y": float(source.y),
                    "width": float(source.width),
                    "height": float(source.height),
                }
                for source in scene.sources
            ]

            snapshot.append(
                {
                    "workspace": workspace,
                    "monitor_name": workspace.monitor_name,
                    "width": float(workspace.width),
                    "height": float(workspace.height),
                    "position": self._program_workspace_position(workspace),
                    "scene": scene,
                    "sources": sources,
                }
            )

        self._program_snapshot = snapshot

    def _program_workspace_position(self, workspace) -> QPointF:
        monitor_name = getattr(workspace, "monitor_name", None)
        position = self._monitor_positions.get(monitor_name)

        if position is not None:
            return self._to_qpointf(position)

        return QPointF(
            float(getattr(workspace, "x", 0)),
            float(getattr(workspace, "y", 0)),
        )

    def render_active_scenes(self, capture_snapshot: bool = True) -> None:
        if capture_snapshot or self._program_snapshot is None:
            self.capture_program_snapshot()

        self._render_program_snapshot()

    def activate_scene_for_program(self, space) -> None:
        self.capture_program_snapshot()
        self._render_program_snapshot()

    def push_scene_to_program(self, space) -> None:
        self.activate_scene_for_program(space)

    def _render_program_snapshot(self) -> None:
        self._rebuild_program_workspaces_from_snapshot()

        for program_workspace_item in self._program_workspace_items:
            state_workspace = program_workspace_item.workspace

            for source_state in getattr(
                state_workspace,
                "_program_sources",
                [],
            ):
                source_definition = source_state["source"]

                item = self.renderer.create_source_item(
                    source_definition
                )

                if item is None:
                    continue

                item.source.x = source_state["x"]
                item.source.y = source_state["y"]
                item.source.width = source_state["width"]
                item.source.height = source_state["height"]

                item.set_source_size(
                    source_state["width"],
                    source_state["height"],
                )

                item.setPos(
                    program_workspace_item.x()
                    + source_state["x"] * self.SCALE,
                    program_workspace_item.y()
                    + source_state["y"] * self.SCALE,
                )

                item.set_editable(False)
                item.owner_space = state_workspace

                self.program_scene.addItem(item)
                self._program_source_items.append(item)

                self._update_program_source_clip(item)

        self._update_program_scene_rect()

    def _rebuild_program_workspaces_from_snapshot(self) -> None:
        self._clear_program_items()

        if self._program_snapshot is None:
            return

        for state in self._program_snapshot:
            class _ProgramWorkspace:
                pass

            workspace = _ProgramWorkspace()
            workspace.name = state["workspace"].name
            workspace.monitor_name = state["monitor_name"]
            workspace.width = state["width"]
            workspace.height = state["height"]
            workspace._program_sources = state["sources"]

            item = WorkspaceItem(
                workspace,
                workspace.width * self.SCALE,
                workspace.height * self.SCALE,
            )

            item.setFlag(
                item.GraphicsItemFlag.ItemIsMovable,
                False,
            )
            item.setFlag(
                item.GraphicsItemFlag.ItemIsSelectable,
                False,
            )
            item.setPos(state["position"])

            self.program_scene.addItem(item)
            self._program_workspace_items.append(item)

        self._update_program_scene_rect()

    def _update_program_source_clip(self, source_item) -> None:
        path = source_item._clip_path.__class__()
        source_rect = source_item.sceneBoundingRect()

        for workspace_item in self._program_workspace_items:
            intersection = source_rect.intersected(
                workspace_item.sceneBoundingRect()
            )

            if intersection.isEmpty():
                continue

            path.addPolygon(
                source_item.mapFromScene(intersection)
            )

        source_item._clip_path = path
        source_item.setVisible(not path.isEmpty())
        source_item.update()

    def _clear_program_items(self) -> None:
        for item in self._program_source_items:
            dispose = getattr(item, "dispose", None)
            if dispose is not None:
                dispose()

            if item.scene() is not None:
                item.scene().removeItem(item)

        self._program_source_items.clear()

        for item in self._program_workspace_items:
            if item.scene() is not None:
                item.scene().removeItem(item)

        self._program_workspace_items.clear()
        self.program_scene.clear()

    def _update_program_scene_rect(self) -> None:
        rect = self.program_scene.itemsBoundingRect()

        if rect.isEmpty():
            rect = QRectF(0, 0, 100, 100)

        self.program_scene.setSceneRect(
            rect.adjusted(-100, -100, 100, 100)
        )

    # ==========================================================
    # DELEGACIÓN
    # ==========================================================

    def get_monitor_item(self, monitor_name):
        return self.renderer.get_workspace_item_for_monitor(
            monitor_name
        )

    def get_program_monitor_item(self, monitor_name):
        for item in self._program_workspace_items:
            if getattr(
                item.workspace,
                "monitor_name",
                None,
            ) == monitor_name:
                return item
        return None

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

    def _to_qpointf(self, position) -> QPointF:
        if isinstance(position, QPointF):
            return QPointF(position)

        return QPointF(
            float(position[0]),
            float(position[1]),
        )

    def _update_view_from_scene(self) -> None:
        self.setScene(self.graphics_scene)

        rect = self.graphics_scene.sceneRect()

        if rect.isNull() or rect.isEmpty():
            return

        self.fitInView(
            rect,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        if (
            self._settings_mode
            and self._settings_scene is not None
        ):
            rect = self._settings_scene.sceneRect()
            if not rect.isEmpty():
                self.fitInView(
                    rect,
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
        elif self.scene() is self.graphics_scene:
            self._update_view_from_scene()
