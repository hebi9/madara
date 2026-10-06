from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsView

from app.ui.workspace.selection_manager import SelectionManager
from app.ui.workspace.workspace_renderer import WorkspaceRenderer
from app.ui.workspace.workspace_scene import WorkspaceScene
from app.ui.widgets.workspace_item import WorkspaceItem


class MonitorLayoutView(QGraphicsView):
    """Editor lógico y constructor del snapshot de Programa.

    Las coordenadas del proyecto son siempre lógicas. Los monitores físicos
    solamente determinan en qué pantalla se presenta cada VirtualSpace y la
    transformación final de resolución se realiza en PlaybackWindow.
    """

    SCALE = 0.15
    GAP = 20
    WORKSPACE_ORIGIN_PADDING = 250
    MIN_ZOOM = 0.05
    MAX_ZOOM = 3.0
    ZOOM_STEP = 1.15

    def __init__(self, workspaces=None, editable=False, monitors=None, parent=None) -> None:
        super().__init__(parent)

        self.editable = editable
        self.virtual_spaces = []
        self.monitors = list(monitors or [])
        self._monitor_positions: dict[str, QPointF] = {}

        self.graphics_scene = WorkspaceScene(self)

        # Cada monitor tiene su propia escena de salida. Así nunca se
        # superponen los VirtualSpace: cada salida siempre empieza en (0, 0)
        # y ocupa exactamente el canvas lógico de su propio EV.
        self.program_scene = WorkspaceScene(self)
        self._program_scenes: dict[str, WorkspaceScene] = {}
        self._program_workspace_by_monitor: dict[str, WorkspaceItem] = {}

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

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._zoom = 1.0

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

        self.renderer.update_scene_rect()
        self._update_view_from_scene()

    def _reset_view_to_workspace_bounds(self) -> None:
        self.resetTransform()
        self._zoom = 1.0

        rect = self.graphics_scene.sceneRect()
        if rect.isNull() or rect.isEmpty():
            return

        padded = rect.adjusted(
            -self.WORKSPACE_ORIGIN_PADDING,
            -self.WORKSPACE_ORIGIN_PADDING,
            self.WORKSPACE_ORIGIN_PADDING,
            self.WORKSPACE_ORIGIN_PADDING,
        )
        self.fitInView(
            padded,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def _apply_zoom(self, factor: float) -> None:
        target = self._zoom * factor
        if target < self.MIN_ZOOM or target > self.MAX_ZOOM:
            return
        self.scale(factor, factor)
        self._zoom = target

    def wheelEvent(self, event) -> None:
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            factor = (
                self.ZOOM_STEP
                if event.angleDelta().y() > 0
                else 1 / self.ZOOM_STEP
            )
            self._apply_zoom(factor)
            event.accept()
            return

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            delta = event.angleDelta().y() or event.angleDelta().x()
            if delta:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - delta
                )
            event.accept()
            return

        super().wheelEvent(event)

    def keyPressEvent(self, event) -> None:
        if (
            event.key() == Qt.Key.Key_0
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self._reset_view_to_workspace_bounds()
            event.accept()
            return
        super().keyPressEvent(event)

    def render_scene_for_editing(self, scene) -> None:
        self._settings_mode = False
        self.setScene(self.graphics_scene)

        self.renderer.render_scene_for_editing(scene)
        self.renderer.update_scene_rect()
        self._update_view_from_scene()

    def adopt_monitor_position(self, workspace) -> None:
        """Usa la posición física como posición inicial al asignar monitor."""
        monitor_name = getattr(workspace, "monitor_name", None)
        if not monitor_name:
            return

        position = self._monitor_positions.get(monitor_name)
        if position is None:
            return

        position = self._to_qpointf(position)
        # Las posiciones físicas están en unidades de escena; el proyecto
        # usa coordenadas lógicas.
        workspace.x = position.x() / self.SCALE
        workspace.y = position.y() / self.SCALE

        for item in self.renderer.workspace_items:
            if item.workspace is workspace:
                item.setPos(position)
                item.refresh_label()
                break

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
            monitor_name = getattr(workspace, "monitor_name", None)
            if not monitor_name:
                continue

            scene = getattr(workspace, "active_scene", None)
            sources = []

            if scene is not None:
                for source in scene.sources:
                    # El proyecto usa coordenadas globales. En reproducción
                    # cada EV es una salida independiente, así que calculamos
                    # la posición local respecto al origen del EV.
                    sources.append(
                        {
                            "source": source,
                            "x": float(source.x) - float(workspace.x),
                            "y": float(source.y) - float(workspace.y),
                            "width": float(source.width),
                            "height": float(source.height),
                            "z_index": int(getattr(source, "z_index", 0)),
                        }
                    )

            snapshot.append(
                {
                    "workspace": workspace,
                    "monitor_name": monitor_name,
                    "width": float(workspace.width),
                    "height": float(workspace.height),
                    "x": float(getattr(workspace, "x", 0.0)),
                    "y": float(getattr(workspace, "y", 0.0)),
                    "scene": scene,
                    "sources": sources,
                }
            )

        self._program_snapshot = snapshot

    def render_active_scenes(self, capture_snapshot: bool = True) -> None:
        if capture_snapshot or self._program_snapshot is None:
            self.capture_program_snapshot()

        self._render_program_snapshot()

    def activate_scene_for_program(self, space) -> None:
        self.capture_program_snapshot()
        self._render_program_snapshot()

    def push_scene_to_program(self, space) -> None:
        self.activate_scene_for_program(space)

    def _create_program_workspace_item(self, state):
        class _ProgramWorkspace:
            pass

        workspace = _ProgramWorkspace()
        workspace.name = state["workspace"].name
        workspace.monitor_name = state["monitor_name"]
        workspace.width = state["width"]
        workspace.height = state["height"]
        workspace.x = 0.0
        workspace.y = 0.0

        item = WorkspaceItem(
            workspace,
            workspace.width * self.SCALE,
            workspace.height * self.SCALE,
        )
        item.position_changed_callback = None
        item.setFlag(
            item.GraphicsItemFlag.ItemIsMovable,
            False,
        )
        item.setFlag(
            item.GraphicsItemFlag.ItemIsSelectable,
            False,
        )
        item.setPos(0, 0)
        return item

    def _render_program_snapshot(self) -> None:
        self._clear_program_items()

        if self._program_snapshot is None:
            return

        for state in self._program_snapshot:
            monitor_name = state["monitor_name"]
            scene = WorkspaceScene(self)
            self._program_scenes[monitor_name] = scene

            # El EV es un canvas lógico. Se deja como metadata visual invisible
            # para que las fuentes no dependan de un rectángulo QGraphicsItem.
            workspace_item = self._create_program_workspace_item(state)
            workspace_rect = QRectF(
                0,
                0,
                state["width"] * self.SCALE,
                state["height"] * self.SCALE,
            )

            ordered_sources = sorted(
                state["sources"],
                key=lambda item: int(item.get("z_index", 0)),
            )

            for source_state in ordered_sources:
                item = self._create_program_source_item(
                    source_state["source"],
                    source_state,
                )
                if item is None:
                    continue

                scene.addItem(item)
                self._program_source_items.append(item)

            # Fondo blanco del EV, debajo de las fuentes.
            background = QGraphicsRectItem(workspace_rect)
            background.setBrush(QColor("white"))
            background.setPen(QPen(Qt.PenStyle.NoPen))
            background.setZValue(-1_000_000)
            scene.addItem(background)

            scene.setSceneRect(workspace_rect)

            # El item tampoco se añade a la escena: solo representa el
            # tamaño/monitor del EV para PlaybackManager.
            self._program_workspace_items.append(workspace_item)
            self._program_workspace_by_monitor[monitor_name] = workspace_item

    def _create_program_source_item(self, source_definition, source_state):
        from app.sources.image_source import ImageSource
        from app.sources.text_source import TextSource
        from app.sources.video_source import VideoSource
        from app.sources.url_source import UrlSource
        from app.ui.sources.image_source_item import ImageSourceItem
        from app.ui.sources.text_source_item import TextSourceItem
        from app.ui.sources.video_source_item import VideoSourceItem
        from app.ui.sources.url_source_item import UrlSourceItem

        source_type = getattr(source_definition, "type", "texto")

        if source_type == "imagen":
            path = getattr(source_definition, "path", "")
            if not path:
                return None
            source = ImageSource.create(path)
            item_cls = ImageSourceItem
        elif source_type == "video":
            path = getattr(source_definition, "path", "")
            if not path:
                return None
            source = VideoSource.create(path)
            item_cls = VideoSourceItem
        elif source_type == "url":
            url = getattr(source_definition, "url", "")
            if not url:
                return None
            source = UrlSource.create(url)
            item_cls = UrlSourceItem
        elif source_type == "texto":
            source = TextSource.create(
                getattr(source_definition, "text", "Nuevo texto")
            )
            item_cls = TextSourceItem
        else:
            return None

        source.x = source_state["x"]
        source.y = source_state["y"]
        source.width = source_state["width"]
        source.height = source_state["height"]

        item = item_cls(
            source=source,
            scale=self.SCALE,
            canvas_width=1,
            canvas_height=1,
            workspace_view=None,
        )
        item.set_editable(False)
        item.set_source_size(
            source_state["width"],
            source_state["height"],
        )
        item.setPos(
            source_state["x"] * self.SCALE,
            source_state["y"] * self.SCALE,
        )
        return item

    def _clear_program_items(self) -> None:
        for item in self._program_source_items:
            dispose = getattr(item, "dispose", None)
            if dispose is not None:
                dispose()

        for scene in self._program_scenes.values():
            scene.clear()

        self._program_scenes.clear()
        self._program_workspace_by_monitor.clear()
        self._program_source_items.clear()
        self._program_workspace_items.clear()

        self.program_scene.clear()

    def get_program_scene(self, monitor_name):
        return self._program_scenes.get(monitor_name)

   # ==========================================================

   # ==========================================================

    def get_monitor_item(self, monitor_name):
        return self.renderer.get_workspace_item_for_monitor(
            monitor_name
        )

    def get_program_monitor_item(self, monitor_name):
        return self._program_workspace_by_monitor.get(monitor_name)

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

        if abs(self._zoom - 1.0) < 1e-9:
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
        elif (
            self.scene() is self.graphics_scene
            and abs(self._zoom - 1.0) < 1e-9
        ):
            self._update_view_from_scene()
