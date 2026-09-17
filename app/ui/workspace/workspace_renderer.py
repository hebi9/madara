from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainterPath

from app.sources.image_source import ImageSource
from app.sources.text_source import TextSource
from app.sources.video_source import VideoSource
from app.sources.url_source import UrlSource
from app.ui.sources.image_source_item import ImageSourceItem
from app.ui.sources.source_item import SourceItem
from app.ui.sources.text_source_item import TextSourceItem
from app.ui.sources.video_source_item import VideoSourceItem
from app.ui.sources.url_source_item import UrlSourceItem
from app.ui.widgets.workspace_item import WorkspaceItem


class WorkspaceRenderer:
    """Construye y mantiene los elementos gráficos del workspace.

    No gestiona la interacción del QGraphicsView ni mantiene el estado
    lógico de selección. Su responsabilidad es transformar los modelos
    de proyecto en QGraphicsItems y mantener su representación.
    """

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

    def set_workspaces(self, workspaces, monitor_positions=None, monitors=None, editable=None) -> None:
        self.virtual_spaces = list(workspaces or [])
        self.monitor_positions = monitor_positions or {}
        self.monitors = list(monitors or [])
        if editable is not None:
            self.editable = editable
        self._create_workspaces()

    def _workspace_position(self, workspace, default_x: float) -> QPointF:
        if getattr(workspace, "monitor_name", None):
            position = self.monitor_positions.get(workspace.monitor_name)
            if position is not None:
                if isinstance(position, QPointF):
                    return position
                return QPointF(position[0], position[1])
        return QPointF(default_x, 0)

    def _create_workspaces(self) -> None:
        self.graphics_scene.clear()
        self.workspace_items.clear()
        self.source_items.clear()

        x = 0.0
        for workspace in self.virtual_spaces:
            width = workspace.width * self.scale
            height = workspace.height * self.scale

            item = WorkspaceItem(workspace, width, height)
            item.setFlag(item.GraphicsItemFlag.ItemIsMovable, self.editable)
            item.setPos(self._workspace_position(workspace, x))
            self.graphics_scene.addItem(item)
            self.workspace_items.append(item)
            x += width + self.gap

        self.update_scene_rect()

    def render_scene_for_editing(self, scene) -> None:
        self._clear_sources()
        if scene is None:
            return

        for source_definition in scene.sources:
            item = self.create_source_item(source_definition)
            if item is None:
                continue
            self.graphics_scene.addItem(item)
            item.set_editable(True)
            self.source_items.append(item)
            self.update_source_clip(item)

    def create_source_item(self, source_definition):
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
        path = QPainterPath()
        source_rect = source_item.sceneBoundingRect()
        clipping_items = clip_items if clip_items is not None else self.workspace_items

        for workspace in clipping_items:
            intersection = source_rect.intersected(workspace.sceneBoundingRect())
            if intersection.isEmpty():
                continue
            local = source_item.mapFromScene(intersection)
            path.addPolygon(local)

        source_item._clip_path = path
        source_item.setVisible(not path.isEmpty())
        source_item.update()

    def constrain_source_position(self, source_item, value):
        return value

    def update_scene_rect(self, margin: float = 100) -> QRectF:
        if not self.workspace_items:
            rect = QRectF(0, 0, 100, 100)
        else:
            rect = QRectF()
            for item in self.workspace_items:
                rect = rect.united(item.sceneBoundingRect())
            rect.adjust(-margin, -margin, margin, margin)
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

    def monitor_positions_snapshot(self):
        positions = {}
        for item in self.workspace_items:
            name = getattr(item.workspace, "name", None)
            if name:
                positions[name] = item.pos()
        return positions
