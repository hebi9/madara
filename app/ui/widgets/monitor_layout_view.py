from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsView,
)

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


class MonitorLayoutView(QGraphicsView):

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

        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)

        # Escena de "Programa" (salida en vivo). Es completamente
        # independiente de la escena de edición/preview: solo se
        # reconstruye mediante acciones explícitas del usuario
        # (activar escena, iniciar reproducción), nunca por el
        # simple hecho de seleccionar/editar algo en el lienzo.
        self.program_scene = QGraphicsScene(self)
        self.program_workspace_items = []
        self.program_source_items = []

        self.setBackgroundBrush(QColor("#2b2b2b"))
        self.setFrameShape(QGraphicsView.NoFrame)

        self.virtual_spaces = list(workspaces or [])
        self.workspace_items = []
        self.source_items = []

        self._monitor_positions = {}
        self.monitors = list(monitors or [])
        self.monitor_items = self.workspace_items

        self._create_workspaces()

    # ==========================================================
    # ESCALA
    # ==========================================================

    def _source_scale(self) -> float:
        return self.SCALE

    # ==========================================================
    # WORKSPACES
    # ==========================================================

    def _workspace_position(
        self,
        workspace,
        default_x: float,
    ) -> QPointF:

        if workspace.monitor_name:

            position = self._monitor_positions.get(
                workspace.monitor_name
            )

            if position is not None:

                if isinstance(position, QPointF):
                    return position

                return QPointF(
                    position[0],
                    position[1],
                )

        return QPointF(default_x, 0)
    

    def _create_workspaces(self):

        self.graphics_scene.clear()
        self.workspace_items.clear()
        self.source_items.clear()

        x = 0

        for workspace in self.virtual_spaces:

            if hasattr(workspace, "geometry"):
                width = workspace.geometry.width() * self.SCALE
                height = workspace.geometry.height() * self.SCALE

                name = workspace.name
                monitor_name = workspace.name

                class _MonitorAdapter:
                    pass

                adapter = _MonitorAdapter()
                adapter.name = name
                adapter.width = workspace.geometry.width()
                adapter.height = workspace.geometry.height()
                adapter.monitor_name = monitor_name

                workspace_obj = adapter

            else:
                width = workspace.width * self.SCALE
                height = workspace.height * self.SCALE
                workspace_obj = workspace

            item = WorkspaceItem(
                workspace_obj,
                width,
                height,
            )
            item.setFlag(
                item.GraphicsItemFlag.ItemIsMovable,
                self.editable,
            )
            item.setPos(
                self._workspace_position(
                    workspace_obj,
                    x,
                )
            )

            self.graphics_scene.addItem(item)
            self.workspace_items.append(item)

            x += width + self.GAP

        self.monitor_items = self.workspace_items

        self._update_scene()

        self._create_program_workspaces()

    def _create_program_workspaces(self):
        """Reconstruye la escena de "Programa" (salida en vivo) para
        que sus rectángulos de monitor/espacio reflejen la misma
        geometría/posición que la escena de edición, pero de forma
        totalmente aislada: nunca comparte objetos con
        ``self.graphics_scene``.
        """

        self._clear_program_sources()

        self.program_scene.clear()
        self.program_workspace_items.clear()

        for workspace_item in self.workspace_items:

            item = WorkspaceItem(
                workspace_item.workspace,
                workspace_item.rect().width(),
                workspace_item.rect().height(),
            )
            item.setFlag(
                item.GraphicsItemFlag.ItemIsMovable,
                False,
            )
            item.setFlag(
                item.GraphicsItemFlag.ItemIsSelectable,
                False,
            )
            item.setPos(workspace_item.pos())

            self.program_scene.addItem(item)
            self.program_workspace_items.append(item)

        if self.program_workspace_items:
            rect = QRectF()
            for item in self.program_workspace_items:
                rect = rect.united(item.sceneBoundingRect())
            self.program_scene.setSceneRect(rect)
        else:
            self.program_scene.setSceneRect(0, 0, 100, 100)

        # Preservar lo que ya estaba activo/en vivo para cada
        # espacio: un cambio de geometría (mover/redimensionar un
        # espacio) no debe apagar la reproducción en curso.
        for workspace_item in self.program_workspace_items:
            scene = getattr(workspace_item.workspace, "active_scene", None)
            if scene is not None:
                self._build_program_sources_for_space(workspace_item, scene)

    def set_workspaces(
        self,
        workspaces,
        monitor_positions=None,
        monitors=None,
    ) -> None:

        self.virtual_spaces = list(workspaces)
        self._monitor_positions = monitor_positions or {}
        self.monitors = list(monitors or [])

        self._create_workspaces()

    def set_monitors(self, monitors, positions=None) -> None:
        self.monitors = list(monitors or [])
        if positions is not None:
            self._monitor_positions = positions
        self.set_workspaces(
            self.monitors,
            self._monitor_positions,
            self.monitors,
        )

    def set_monitor_positions(self, positions) -> None:
        self._monitor_positions = positions or {}
        self._create_workspaces()

    def monitor_positions(self):
        positions = {}
        for item in self.workspace_items:
            name = getattr(item.workspace, "name", None)
            if name:
                positions[name] = item.pos()
        return positions

    # ==========================================================
    # SCENE
    # ==========================================================

    def _update_scene(self):

        if not self.workspace_items:
            self.graphics_scene.setSceneRect(
                0,
                0,
                100,
                100,
            )
            return

        rect = QRectF()

        for item in self.workspace_items:
            rect = rect.united(
                item.sceneBoundingRect()
            )

        rect.adjust(
            -100,
            -100,
            100,
            100,
        )

        self.graphics_scene.setSceneRect(rect)

        self.fitInView(
            rect,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    # ==========================================================
    # RENDER
    # ==========================================================

    def _clear_sources(self):

        for item in self.source_items:

            dispose = getattr(item, "dispose", None)
            if dispose is not None:
                dispose()

            if item.scene() is not None:
                self.graphics_scene.removeItem(item)

        self.source_items.clear()

    def _clear_program_sources(self, only_space=None):
        """Elimina las fuentes de la escena de Programa.

        Si ``only_space`` se indica, solo se eliminan las fuentes que
        pertenecen a ese espacio (permite actualizar un espacio sin
        afectar lo que ya se está reproduciendo en los demás).
        """

        remaining = []

        for item in self.program_source_items:

            owner_space = getattr(item, "owner_space", None)

            if only_space is not None and owner_space is not only_space:
                remaining.append(item)
                continue

            dispose = getattr(item, "dispose", None)
            if dispose is not None:
                dispose()

            if item.scene() is not None:
                self.program_scene.removeItem(item)

        self.program_source_items = remaining

    def render_scene_for_editing(
        self,
        scene,
    ):

        self._clear_sources()

        if scene is None:
            self._update_scene()
            return

        for source_definition in scene.sources:

            item = self._create_source_item(
                source_definition
            )

            if item is None:
                continue

            self.graphics_scene.addItem(item)
            item.set_editable(True)
            self.source_items.append(item)

            self.update_source_clip(item)

        self._update_scene()

    def render_active_scenes(self):
        """Reconstruye TODA la escena de Programa (salida en vivo)
        a partir de la escena activa de cada espacio. Debe invocarse
        solo desde acciones explícitas del usuario (iniciar
        reproducción, etc.), nunca como efecto secundario de editar
        o seleccionar algo en el lienzo.
        """

        self._clear_program_sources()

        for workspace_item in self.program_workspace_items:
            workspace = workspace_item.workspace
            scene = getattr(workspace, "active_scene", None)
            if scene is None:
                continue

            self._build_program_sources_for_space(workspace_item, scene)

        if self.program_workspace_items:
            rect = QRectF()
            for item in self.program_workspace_items:
                rect = rect.united(item.sceneBoundingRect())
            self.program_scene.setSceneRect(rect)

    def push_scene_to_program(self, space) -> None:
        """Actualiza únicamente la salida en vivo del espacio dado,
        sin tocar lo que ya se muestra para los demás espacios. Es
        el mecanismo explícito para "activar" una escena en el
        Programa.
        """

        workspace_item = None
        for item in self.program_workspace_items:
            if item.workspace is space:
                workspace_item = item
                break

        if workspace_item is None:
            return

        self._clear_program_sources(only_space=space)

        scene = getattr(space, "active_scene", None)
        if scene is not None:
            self._build_program_sources_for_space(workspace_item, scene)

    def _build_program_sources_for_space(self, workspace_item, scene) -> None:
        space = workspace_item.workspace

        for source_definition in scene.sources:
            item = self._create_source_item(source_definition)
            if item is None:
                continue

            item.setPos(
                workspace_item.x() + source_definition.x * self.SCALE,
                workspace_item.y() + source_definition.y * self.SCALE,
            )
            item.owner_space = space
            self.program_scene.addItem(item)
            item.set_editable(False)
            self.program_source_items.append(item)
            self.update_source_clip(
                item,
                clip_items=self.program_workspace_items,
            )

    def get_monitor_item(self, monitor_name):
        for item in self.workspace_items:
            workspace = item.workspace
            if getattr(workspace, "monitor_name", None) == monitor_name:
                return item
        return None

    def get_program_monitor_item(self, monitor_name):
        for item in self.program_workspace_items:
            workspace = item.workspace
            if getattr(workspace, "monitor_name", None) == monitor_name:
                return item
        return None

    def _create_source_item(
        self,
        source_definition,
    ):

        scale = self._source_scale()

        source_type = getattr(
            source_definition,
            "type",
            "texto",
        )

        if source_type == "imagen":

            path = getattr(
                source_definition,
                "path",
                "",
            )

            if not path:
                return None

            source = ImageSource.create(path)

        elif source_type == "video":

            path = getattr(source_definition, "path", "")
            if not path:
                return None
            source = VideoSource.create(path)

        elif source_type == "url":

            url = getattr(source_definition, "url", "")
            if not url:
                return None
            source = UrlSource.create(url)

        elif source_type == "texto":

            source = TextSource.create(
                getattr(
                    source_definition,
                    "text",
                    "Nuevo texto",
                )
            )

        else:
            return None

        source.x = source_definition.x
        source.y = source_definition.y
        source.width = source_definition.width
        source.height = source_definition.height

        if source_type == "imagen":

            item = ImageSourceItem(
                source=source,
                scale=scale,
                canvas_width=1,
                canvas_height=1,
                workspace_view=self,
            )

        elif source_type == "video":

            item = VideoSourceItem(
                source=source,
                scale=scale,
                canvas_width=1,
                canvas_height=1,
                workspace_view=self,
            )

        elif source_type == "url":

            item = UrlSourceItem(
                source=source,
                scale=scale,
                canvas_width=1,
                canvas_height=1,
                workspace_view=self,
            )

        else:

            item = TextSourceItem(
                source=source,
                scale=scale,
                canvas_width=1,
                canvas_height=1,
                workspace_view=self,
            )

        item.source_definition = source_definition

        item.set_source_position(
            source_definition.x,
            source_definition.y,
        )

        item.set_source_size(
            source_definition.width,
            source_definition.height,
        )

        return item

    # ==========================================================
    # CLIPPING
    # ==========================================================

    def update_source_clip(
        self,
        source_item,
        clip_items=None,
    ) -> None:

        path = QPainterPath()

        source_rect = source_item.sceneBoundingRect()

        clipping_items = (
            clip_items
            if clip_items is not None
            else (self.monitor_items or self.workspace_items)
        )

        for workspace in clipping_items:

            intersection = source_rect.intersected(
                workspace.sceneBoundingRect()
            )

            if intersection.isEmpty():
                continue

            local = source_item.mapFromScene(
                intersection
            )
            path.addPolygon(local)

        source_item._clip_path = path
        source_item.setVisible(not path.isEmpty())
        source_item.update()

    # ==========================================================
    # MOVIMIENTO
    # ==========================================================

    def constrain_source_position(
        self,
        source_item,
        value,
    ):
        return value

    # ==========================================================
    # SELECCIÓN
    # ==========================================================

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

    def get_workspace_from_item(
        self,
        item,
    ):

        if isinstance(item, WorkspaceItem):
            return item

        return None

    # ==========================================================
    # QT
    # ==========================================================

    def resizeEvent(
        self,
        event,
    ) -> None:

        super().resizeEvent(event)

        self._update_scene()
