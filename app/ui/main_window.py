from __future__ import annotations

import sys

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.models.project import Scene, SourceDefinition, VirtualSpace
from app.config.monitor_config import MonitorConfig
from app.config.project_state import ProjectState
from app.config.shortcut_config import ShortcutConfig
from app.playback.playback_manager import PlaybackManager
from app.services.monitor_service import MonitorService
from app.ui.dialogs.settings_dialog import SettingsDialog
from app.ui.panels.properties_panel import PropertiesPanel
from app.ui.panels.workspace_panels import EntityListPanel
from app.ui.widgets.monitor_layout_view import MonitorLayoutView


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Scene Player")
        self.resize(1440, 1080)

        self.sidebar_expanded = True
        self.playback_manager = PlaybackManager()
        self.shortcuts = ShortcutConfig.load()

        # Estado del proyecto: se restaura al iniciar y se guarda en disco
        # automáticamente ante cambios relevantes y al cerrar la aplicación.
        self.virtual_spaces, self.scenes = ProjectState.load()

        self.selected_space: VirtualSpace | None = None
        self.selected_scene: Scene | None = None
        self._last_space_monitor_names: dict[int, str | None] = {}

        self.monitors = MonitorService.list_monitors()
        saved_active_monitors, saved_positions = MonitorConfig.load()

        if saved_active_monitors:
            self.active_monitor_names = {
                monitor.name
                for monitor in self.monitors
                if monitor.name in saved_active_monitors
            }
        else:
            self.active_monitor_names = {
                monitor.name for monitor in self.monitors
            }

        self.monitor_positions: dict[str, QPointF] = saved_positions

        self._setup_ui()
        self._setup_shortcuts()
        self._restore_initial_selection()

    def _restore_initial_selection(self) -> None:
        if self.virtual_spaces:
            space = self.virtual_spaces[0]
            self.spaces_panel.list_widget.setCurrentRow(0)
            self._space_selected(space)

        if self.scenes:
            scene = self.scenes[0]
            self.scenes_panel.list_widget.setCurrentRow(0)
            self._scene_selected(scene)
        elif self.virtual_spaces:
            scene = self._create_scene(self.virtual_spaces[0])
            self._scene_selected(scene)

        self._render_active_scenes()

    def _save_project_state(self) -> None:
        ProjectState.save(self.virtual_spaces, self.scenes)

    # ==========================================================
    # MONITORES
    # ==========================================================

    def _get_active_monitors(self):
        return [
            monitor
            for monitor in self.monitors
            if monitor.name in self.active_monitor_names
        ]

    # ==========================================================
    # UI
    # ==========================================================

    def _render_active_scenes(self) -> None:
        self.monitor_view.render_active_scenes()

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)

        self.toggle_button = QPushButton("☰")
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        sidebar_layout.addWidget(self.toggle_button)

        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.toggle_playback)
        sidebar_layout.addWidget(self.play_button)
        sidebar_layout.addStretch()

        self.settings_button = QPushButton("⚙ Configuración")
        self.settings_button.clicked.connect(self.open_settings)
        sidebar_layout.addWidget(self.settings_button)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(6)

        toolbar = QHBoxLayout()
        self.add_image_button = QPushButton("+ Imagen")
        self.add_text_button = QPushButton("+ Texto")
        self.add_video_button = QPushButton("+ Video")
        self.add_url_button = QPushButton("+ URL")
        self.delete_source_button = QPushButton("Eliminar")
        self.delete_source_button.setEnabled(False)
        self.activate_scene_button = QPushButton("▶ Activar en Programa")
        self.activate_scene_button.setEnabled(False)

        self.add_image_button.clicked.connect(self.add_image_source)
        self.add_text_button.clicked.connect(self.add_text_source)
        self.add_video_button.clicked.connect(self.add_video_source)
        self.add_url_button.clicked.connect(self.add_url_source)
        self.delete_source_button.clicked.connect(self.delete_selected_source)
        self.activate_scene_button.clicked.connect(self._activate_selected_scene)

        toolbar.addWidget(self.add_image_button)
        toolbar.addWidget(self.add_text_button)
        toolbar.addWidget(self.add_video_button)
        toolbar.addWidget(self.add_url_button)
        toolbar.addWidget(self.delete_source_button)
        toolbar.addStretch()
        toolbar.addWidget(self.activate_scene_button)
        content_layout.addLayout(toolbar)

        self.monitor_view = MonitorLayoutView(
            self.virtual_spaces,
            editable=False,
            monitors=self.monitors,
        )
        self.monitor_view.set_workspaces(
            self.virtual_spaces,
            self.monitor_positions,
            self.monitors,
        )

        self.properties_panel = PropertiesPanel()
        self.properties_panel.set_context(
            self.monitors,
            self.virtual_spaces,
            self.active_monitor_names,
        )
        self.properties_panel.object_changed.connect(self._property_changed)

        workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        workspace_splitter.addWidget(self.monitor_view)
        workspace_splitter.addWidget(self.properties_panel)
        workspace_splitter.setStretchFactor(0, 1)
        workspace_splitter.setStretchFactor(1, 0)
        workspace_splitter.setSizes([1000, 280])
        content_layout.addWidget(workspace_splitter, stretch=1)

        self.spaces_panel = EntityListPanel("Espacios virtuales")
        self.scenes_panel = EntityListPanel("Escenas")
        self.sources_panel = EntityListPanel("Fuentes")

        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(self.spaces_panel)
        bottom_splitter.addWidget(self.scenes_panel)
        bottom_splitter.addWidget(self.sources_panel)
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 1)
        bottom_splitter.setStretchFactor(2, 1)
        bottom_splitter.setSizes([300, 300, 300])
        content_layout.addWidget(bottom_splitter)

        self.monitor_view.graphics_scene.selectionChanged.connect(
            self._view_selection_changed
        )
        self.spaces_panel.item_selected.connect(self._space_selected)
        self.scenes_panel.item_selected.connect(self._scene_selected)
        self.sources_panel.item_selected.connect(self._source_selected)
        self.spaces_panel.item_renamed.connect(self._rename_space)
        self.scenes_panel.item_renamed.connect(self._rename_scene)
        self.sources_panel.item_renamed.connect(self._rename_source)
        self.spaces_panel.item_created.connect(self._create_space)
        self.scenes_panel.item_created.connect(self._create_scene)
        self.sources_panel.item_created.connect(self._create_source)
        self.spaces_panel.item_deleted.connect(self._delete_space)
        self.scenes_panel.item_deleted.connect(self._delete_scene)
        self.sources_panel.item_deleted.connect(self._delete_source)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content, stretch=1)

    # ==========================================================
    # SIDEBAR / SHORTCUTS
    # ==========================================================

    def _update_play_button_text(self) -> None:
        if self.sidebar_expanded:
            self.play_button.setText(
                "■ Detener" if self.playback_manager.is_playing else "▶ Play"
            )
        else:
            self.play_button.setText(
                "■" if self.playback_manager.is_playing else "▶"
            )

    def toggle_sidebar(self) -> None:
        if self.sidebar_expanded:
            self.sidebar.setFixedWidth(60)
            self.settings_button.setText("⚙")
        else:
            self.sidebar.setFixedWidth(200)
            self.settings_button.setText("⚙ Configuración")
        self.sidebar_expanded = not self.sidebar_expanded
        self._update_play_button_text()

    def _setup_shortcuts(self) -> None:
        for shortcut_name in ("play_shortcut", "stop_shortcut"):
            shortcut = getattr(self, shortcut_name, None)
            if shortcut is not None:
                shortcut.deleteLater()

        self.play_shortcut = QShortcut(
            QKeySequence(self.shortcuts.get("play", "")), self
        )
        self.play_shortcut.activated.connect(self._start_playback)

        self.stop_shortcut = QShortcut(
            QKeySequence(self.shortcuts.get("stop", "")), self
        )
        self.stop_shortcut.activated.connect(self._stop_playback)

    def _start_playback(self) -> None:
        if not self.playback_manager.is_playing:
            self.toggle_playback()

    def _stop_playback(self) -> None:
        if self.playback_manager.is_playing:
            self.toggle_playback()

    # ==========================================================
    # PLAYBACK
    # ==========================================================

    def toggle_playback(self) -> None:
        if self.playback_manager.is_playing:
            self.playback_manager.stop()
        else:
            self.monitor_view.render_active_scenes()
            self.playback_manager.play(
                self.monitor_view,
                self.active_monitor_names,
            )
        self._update_play_button_text()

    # ==========================================================
    # CONFIGURACIÓN DE MONITORES
    # ==========================================================

    def open_settings(self) -> None:
        dialog = SettingsDialog(
            active_monitor_names=self.active_monitor_names,
            monitor_positions=self.monitor_positions,
            shortcuts=self.shortcuts,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.active_monitor_names = dialog.selected_monitor_names()
        self.monitor_positions = dialog.selected_monitor_positions()
        MonitorConfig.save(self.active_monitor_names, self.monitor_positions)

        self.shortcuts = dialog.selected_shortcuts()
        ShortcutConfig.save(self.shortcuts)
        self._setup_shortcuts()
        self._refresh_workspace_positions()
        self._save_project_state()

    def _refresh_workspace_positions(self) -> None:
        self.monitor_view.set_workspaces(
            self.virtual_spaces,
            self.monitor_positions,
            self.monitors,
        )
        self.properties_panel.set_context(
            self.monitors,
            self.virtual_spaces,
            self.active_monitor_names,
        )
        if self.selected_space is not None:
            self.properties_panel.set_object(self.selected_space)

    # ==========================================================
    # FUENTES
    # ==========================================================

    def add_image_source(self) -> None:
        if self.selected_scene is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not path:
            return

        source = SourceDefinition(
            name=f"Imagen {len(self.selected_scene.sources) + 1}",
            type="imagen",
            x=0,
            y=0,
            width=400,
            height=300,
            path=path,
        )
        self.selected_scene.sources.append(source)
        self._refresh_sources_for_scene(self.selected_scene)
        self._render_selected_scene()
        self.sources_panel.list_widget.setCurrentRow(
            len(self.selected_scene.sources) - 1
        )

    def _add_file_source(self, source_type: str, title: str, name_prefix: str, file_filter: str) -> None:
        if self.selected_scene is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if not path:
            return
        source = SourceDefinition(
            name=f"{name_prefix} {len(self.selected_scene.sources) + 1}",
            type=source_type,
            x=0,
            y=0,
            width=640 if source_type == "video" else 400,
            height=360 if source_type == "video" else 300,
            path=path,
        )
        self.selected_scene.sources.append(source)
        self._refresh_sources_for_scene(self.selected_scene)
        self._render_selected_scene()
        self.sources_panel.list_widget.setCurrentRow(
            len(self.selected_scene.sources) - 1
        )

    def add_video_source(self) -> None:
        self._add_file_source(
            "video",
            "Seleccionar video",
            "Video",
            "Videos (*.mp4 *.mov *.avi *.mkv *.webm *.m4v)",
        )

    def add_url_source(self) -> None:
        if self.selected_scene is None:
            return
        url, accepted = QInputDialog.getText(
            self,
            "Agregar fuente de internet",
            "URL (https://...):",
        )
        if not accepted or not url.strip():
            return
        source = SourceDefinition(
            name=f"Internet {len(self.selected_scene.sources) + 1}",
            type="url",
            x=0,
            y=0,
            width=800,
            height=450,
            url=url.strip(),
        )
        self.selected_scene.sources.append(source)
        self._refresh_sources_for_scene(self.selected_scene)
        self._render_selected_scene()
        self.sources_panel.list_widget.setCurrentRow(
            len(self.selected_scene.sources) - 1
        )

    def add_text_source(self) -> None:
        if self.selected_scene is None:
            return
        source = SourceDefinition(
            name=f"Texto {len(self.selected_scene.sources) + 1}",
            type="texto",
            x=0,
            y=0,
            width=400,
            height=300,
            text="Nuevo texto",
        )
        self.selected_scene.sources.append(source)
        self._refresh_sources_for_scene(self.selected_scene)
        self._render_selected_scene()
        self.sources_panel.list_widget.setCurrentRow(
            len(self.selected_scene.sources) - 1
        )

    def delete_selected_source(self) -> None:
        source_item = self.monitor_view.get_selected_source()
        if source_item is None:
            return
        source_definition = getattr(source_item, "source_definition", None)
        if source_definition is None or self.selected_scene is None:
            return
        self._delete_source(source_definition)

    # ==========================================================
    # SELECCIÓN
    # ==========================================================

    def _view_selection_changed(self) -> None:
        selected_items = self.monitor_view.graphics_scene.selectedItems()
        if not selected_items:
            self.properties_panel.set_object(None)
            self.delete_source_button.setEnabled(False)
            return

        for item in selected_items:
            if hasattr(item, "workspace") and hasattr(item.workspace, "monitor_name"):
                self._space_selected(item.workspace)
                return
            if hasattr(item, "source"):
                self.properties_panel.set_object(item.source)
                self.delete_source_button.setEnabled(True)
                return

    # ==========================================================
    # ESPACIOS
    # ==========================================================

    def _create_space(self):
        assigned_monitors = {
            space.monitor_name
            for space in self.virtual_spaces
            if space.monitor_name
        }
        available_monitor = next(
            (
                monitor.name
                for monitor in self._get_active_monitors()
                if monitor.name not in assigned_monitors
            ),
            None,
        )

        space = VirtualSpace(
            name=f"Espacio {len(self.virtual_spaces) + 1}",
            width=1920,
            height=1080,
            monitor_name=available_monitor,
        )
        self.virtual_spaces.append(space)
        self._refresh_spaces()
        self.spaces_panel.list_widget.setCurrentRow(len(self.virtual_spaces) - 1)
        self._save_project_state()
        return space

    def _space_selected(self, space) -> None:
        self.selected_space = space
        self.properties_panel.set_object(space)
        self._update_activate_button_state()

    def _delete_space(self, space) -> None:
        if space in self.virtual_spaces:
            self.virtual_spaces.remove(space)
        if self.selected_space is space:
            self.selected_space = None
            self.properties_panel.set_object(None)
        self._refresh_spaces()
        self._update_activate_button_state()
        self._save_project_state()

    def _refresh_spaces(self):
        self.spaces_panel.set_items(
            self.virtual_spaces,
            lambda item: f"{item.name}  •  {item.width} × {item.height}",
        )
        self.monitor_view.set_workspaces(
            self.virtual_spaces,
            self.monitor_positions,
            self.monitors,
        )
        self.properties_panel.set_context(
            self.monitors,
            self.virtual_spaces,
            self.active_monitor_names,
        )
        if self.selected_space in self.virtual_spaces:
            self.spaces_panel.list_widget.setCurrentRow(
                self.virtual_spaces.index(self.selected_space)
            )

    # ==========================================================
    # ESCENAS
    # ==========================================================

    def _create_scene(self, space=None):
        scene = Scene(name=f"Escena {len(self.scenes) + 1}")
        self.scenes.append(scene)
        if space is not None and space.active_scene is None:
            space.active_scene = scene
        self._refresh_scenes()
        self.scenes_panel.list_widget.setCurrentRow(len(self.scenes) - 1)
        self._save_project_state()
        return scene

    def _scene_selected(self, scene) -> None:
        self.selected_scene = scene
        self.properties_panel.set_object(scene)
        self._refresh_sources_for_scene(scene)
        if scene.sources:
            self.sources_panel.list_widget.setCurrentRow(0)
        self.monitor_view.render_scene_for_editing(scene)
        self._update_activate_button_state()

    def _refresh_scenes(self) -> None:
        self.scenes_panel.set_items(self.scenes, lambda scene: scene.name)
        if self.selected_scene in self.scenes:
            self.scenes_panel.list_widget.setCurrentRow(self.scenes.index(self.selected_scene))

    def _delete_scene(self, scene) -> None:
        if scene not in self.scenes:
            return
        self.scenes.remove(scene)
        for space in self.virtual_spaces:
            if space.active_scene is scene:
                space.active_scene = None
        if self.selected_scene is scene:
            self.selected_scene = None
        self._refresh_scenes()
        self._refresh_sources_for_scene(None)
        self.properties_panel.set_object(None)
        self.monitor_view.render_active_scenes()
        self._update_activate_button_state()
        self._save_project_state()

    # ==========================================================
    # FUENTES DE ESCENA
    # ==========================================================

    def _create_source(self) -> None:
        if self.selected_scene is None:
            return
        source_kind, accepted = QInputDialog.getItem(
            self,
            "Nueva fuente",
            "Tipo:",
            ["Imagen", "Texto", "Video", "URL"],
            0,
            False,
        )
        if not accepted:
            return
        {
            "Imagen": self.add_image_source,
            "Texto": self.add_text_source,
            "Video": self.add_video_source,
            "URL": self.add_url_source,
        }[source_kind]()

    def _refresh_sources_for_scene(self, scene: Scene | None) -> None:
        if scene is None:
            self.sources_panel.set_items([], lambda source: source.name)
            return
        self.sources_panel.set_items(
            scene.sources,
            lambda source: f"{source.name}  •  {source.type}",
        )

    def _source_selected(self, source: SourceDefinition) -> None:
        self.properties_panel.set_object(source)

    def _delete_source(self, source) -> None:
        if self.selected_scene is None:
            return
        if source in self.selected_scene.sources:
            self.selected_scene.sources.remove(source)
        self._refresh_sources_for_scene(self.selected_scene)
        self.properties_panel.set_object(None)
        self.monitor_view.render_scene_for_editing(self.selected_scene)
        self._save_project_state()

    # ==========================================================
    # CAMBIOS DE PROPIEDADES / ACTIVACIÓN
    # ==========================================================

    def _property_changed(self, obj) -> None:
        if isinstance(obj, VirtualSpace):
            self._last_space_monitor_names[id(obj)] = obj.monitor_name
            self._refresh_spaces()
            self.monitor_view.render_active_scenes()
        elif isinstance(obj, SourceDefinition):
            self._refresh_sources_for_scene(self.selected_scene)
            self.monitor_view.render_scene_for_editing(self.selected_scene)
        elif isinstance(obj, Scene):
            self._refresh_scenes()
            self.monitor_view.render_scene_for_editing(self.selected_scene)
        self._save_project_state()

    def _rename_space(self, space, name: str) -> None:
        space.name = name.strip() or space.name
        self._refresh_spaces()
        self._save_project_state()

    def _rename_scene(self, scene, name: str) -> None:
        scene.name = name.strip() or scene.name
        self._refresh_scenes()
        self._save_project_state()

    def _rename_source(self, source, name: str) -> None:
        source.name = name.strip() or source.name
        self._refresh_sources_for_scene(self.selected_scene)
        self._save_project_state()

    def activate_scene_for_space(self, space: VirtualSpace, scene: Scene) -> None:
        if scene not in self.scenes or space not in self.virtual_spaces:
            return
        space.active_scene = scene
        self.monitor_view.push_scene_to_program(space)
        self._save_project_state()

    def _update_activate_button_state(self) -> None:
        self.activate_scene_button.setEnabled(
            self.selected_space is not None and self.selected_scene is not None
        )

    def _activate_selected_scene(self) -> None:
        if self.selected_space is None or self.selected_scene is None:
            return
        self.activate_scene_for_space(self.selected_space, self.selected_scene)

    def _render_selected_scene(self) -> None:
        if self.selected_scene is None:
            return
        self.monitor_view.render_scene_for_editing(self.selected_scene)
        self._save_project_state()

    # ==========================================================
    # CIERRE
    # ==========================================================

    def closeEvent(self, event) -> None:
        self.playback_manager.stop()
        self._save_project_state()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
