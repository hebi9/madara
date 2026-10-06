from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QGraphicsItem

from app.ui.sources.source_item import SourceItem
from app.ui.widgets.workspace_item import WorkspaceItem


class WorkspaceRenderer:
    """Renderiza únicamente el editor lógico."""

    def __init__(self, graphics_scene, scale: float = 0.15, gap: float = 60) -> None:
        self.graphics_scene = graphics_scene
        self.scale = scale
        self.gap = gap
        self.virtual_spaces = []
        self.workspace_items = []
        self.source_items = []
        self.monitor_positions = {}
        self.monitors = []
        self.editable = False
        self._known_workspace_ids: set[int] = set()
        self._workspace_state_initialized = False

    def set_workspaces(self, workspaces, monitor_positions=None, monitors=None, editable=None) -> None:
        incoming = list(workspaces or [])

        # La primera carga respeta exactamente las posiciones guardadas en el
        # proyecto. En llamadas posteriores, cualquier VirtualSpace nuevo nace
        # en el origen. Así no inventamos una cuadrícula ni un espaciado.
        if self._workspace_state_initialized:
            for workspace in incoming:
                if id(workspace) not in self._known_workspace_ids:
                    workspace.x = 0.0
                    workspace.y = 0.0
        else:
            self._workspace_state_initialized = True

        self._known_workspace_ids = {id(workspace) for workspace in incoming}
        self.virtual_spaces = incoming
        self.monitor_positions = monitor_positions or {}
        self.monitors = list(monitors or [])
        if editable is not None:
            self.editable = editable
        self._create_workspaces()

    def clear(self) -> None:
        self._clear_sources()
        self.graphics_scene.clear()
        self.workspace_items.clear()

    def _workspace_position(self, workspace, default_x: float) -> QPointF:
        return QPointF(
            float(getattr(workspace, "x", default_x)),
            float(getattr(workspace, "y", 0)),
        )

    def _create_workspaces(self) -> None:
        self._clear_sources()
        self.graphics_scene.clear()
        self.workspace_items.clear()

        for workspace in self.virtual_spaces:
            width = workspace.width * self.scale
            height = workspace.height * self.scale
            item = WorkspaceItem(workspace, width, height)
            item.logical_scale = self.scale
            item.position_changed_callback = self._workspace_position_changed
            item.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
                self.editable and not bool(getattr(workspace, "locked", False)),
            )
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            position = self._workspace_position(workspace, 0.0)
            item.setPos(position.x() * self.scale, position.y() * self.scale)
            self.graphics_scene.addItem(item)
            self.workspace_items.append(item)

        self.update_scene_rect()

    def render_scene_for_editing(self, scene) -> None:
        """Renderiza la escena seleccionada sin tocar el estado del programa."""
        self._clear_sources()
        for item in self.workspace_items:
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        if scene is None:
            return

        ordered_sources = sorted(
            scene.sources,
            key=lambda source: getattr(source, "z_index", 0),
        )

        for source_definition in ordered_sources:
            item = self.create_source_item(source_definition)
            if item is None:
                continue
            self.graphics_scene.addItem(item)
            item.set_editable(self.editable)
            self.source_items.append(item)
            self.update_source_clip(item)

    def create_source_item(self, source_definition):
        from app.sources.image_source import ImageSource
        from app.sources.text_source import TextSource
        from app.sources.video_source import VideoSource
        from app.sources.url_source import UrlSource
        from app.ui.sources.image_source_item import ImageSourceItem
        from app.ui.sources.text_source_item import TextSourceItem
        from app.ui.sources.video_source_item import VideoSourceItem
        from app.ui.sources.url_source_item import UrlSourceItem

        source_type = getattr(source_definition, "type", "texto")
        path = getattr(source_definition, "path", "")

        if source_type == "imagen":
            if not path:
                return None
            source = ImageSource.create(path)
            item_cls = ImageSourceItem
        elif source_type == "video":
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
            source = TextSource.create(getattr(source_definition, "text", "Nuevo texto"))
            item_cls = TextSourceItem
        else:
            return None

        source.x = source_definition.x
        source.y = source_definition.y
        source.width = source_definition.width
        source.height = source_definition.height

        item = item_cls(
            source=source,
            scale=self.scale,
            canvas_width=1,
            canvas_height=1,
            workspace_view=self,
        )
        item.source_definition = source_definition
        item.set_source_position(source_definition.x, source_definition.y)
        item.set_source_size(source_definition.width, source_definition.height)
        return item

    def _clear_sources(self) -> None:
        for item in self.source_items:
            dispose = getattr(item, "dispose", None)
            if dispose is not None:
                dispose()
            if item.scene() is not None:
                self.graphics_scene.removeItem(item)
        self.source_items.clear()

    def update_source_clip(self, source_item, clip_items=None) -> None:
        path = source_item._clip_path.__class__()
        source_rect = source_item.sceneBoundingRect()
        clipping_items = clip_items if clip_items is not None else self.workspace_items

        for workspace in clipping_items:
            intersection = source_rect.intersected(workspace.sceneBoundingRect())
            if intersection.isEmpty():
                continue
            path.addPolygon(source_item.mapFromScene(intersection))

        source_item._clip_path = path
        source_item.setVisible(not path.isEmpty())
        source_item.update()

    def constrain_source_position(self, source_item, value):
        return value

    def _workspace_position_changed(self) -> None:
        # Los EV son máscaras de clipping: moverlos no mueve las fuentes.
        # Sí debemos recalcular qué parte de cada fuente queda visible.
        for source_item in self.source_items:
            self.update_source_clip(source_item)

        self.update_scene_rect()

    def update_scene_rect(self, margin: float = 40) -> QRectF:
        """Ajusta el canvas al rectángulo invisible que engloba todos los EV."""
        if not self.workspace_items:
            rect = QRectF(0, 0, 100, 100)
        else:
            rect = QRectF()
            for item in self.workspace_items:
                rect = rect.united(item.sceneBoundingRect())
            rect = rect.adjusted(-margin, -margin, margin, margin)

        self.graphics_scene.setSceneRect(rect)
        return rect

    def get_selected_source(self):
        for item in self.graphics_scene.selectedItems():
            if isinstance(item, SourceItem):
                return item
        return None

    def get_selected_workspace(self):
        for item in self.graphics_scene.selectedItems():
            if isinstance(item, WorkspaceItem):
                return item.workspace
        return None

    def get_workspace_from_item(self, item):
        return item if isinstance(item, WorkspaceItem) else None

    def get_workspace_item_for_monitor(self, monitor_name):
        for item in self.workspace_items:
            if getattr(item.workspace, "monitor_name", None) == monitor_name:
                return item
        return None
