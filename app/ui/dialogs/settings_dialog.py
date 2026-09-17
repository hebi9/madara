from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.monitor_service import MonitorInfo, MonitorService
from app.ui.widgets.monitor_layout_view import MonitorLayoutView
from PySide6.QtWidgets import QGraphicsView


class SettingsDialog(QDialog):

    def __init__(
        self,
        active_monitor_names: set[str] | None = None,
        monitor_positions: dict[str, QPointF] | None = None,
        shortcuts: dict[str, str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Configuración")
        self.resize(1440, 1080)

        self.monitors = MonitorService.list_monitors()
        self.active_monitor_names = (
            set(active_monitor_names)
            if active_monitor_names is not None
            else {monitor.name for monitor in self.monitors}
        )
        self.monitor_positions = dict(monitor_positions or {})
        self.shortcuts = shortcuts or {
            "play": "Ctrl+P",
            "stop": "Ctrl+Shift+P",
        }
        self._checkboxes: dict[str, QCheckBox] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        content_layout = QHBoxLayout()

        self.navigation = QListWidget()
        self.navigation.setFixedWidth(180)
        self.navigation.addItem(QListWidgetItem("Pantallas"))
        self.navigation.addItem(QListWidgetItem("Atajos de teclado"))
        self.navigation.setCurrentRow(0)
        content_layout.addWidget(self.navigation)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._create_screens_page())
        self.pages.addWidget(self._create_shortcuts_page())
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        content_layout.addWidget(self.pages, stretch=1)
        main_layout.addLayout(content_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _create_screens_page(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)

        title = QLabel("Pantallas")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(
            "Seleccione las pantallas que utilizará la aplicación. "
            "Después puede arrastrarlas para establecer su disposición."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        selection = QWidget()
        selection_layout = QVBoxLayout(selection)
        selection_layout.setContentsMargins(0, 10, 0, 10)

        for monitor in self.monitors:
            checkbox = QCheckBox(monitor.display_name)
            checkbox.setChecked(monitor.name in self.active_monitor_names)
            checkbox.toggled.connect(self._active_monitors_changed)
            self._checkboxes[monitor.name] = checkbox
            selection_layout.addWidget(checkbox)

        layout.addWidget(selection)

        layout_title = QLabel("Disposición")
        layout_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(layout_title)

        # La configuración física debe mostrar siempre los monitores reales,
        # sin pasar por VirtualSpace ni por la escena del programa.
        self.monitor_view = MonitorLayoutView(
            self._get_active_monitors(),
            editable=True,
        )
        self.monitor_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.monitor_view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.monitor_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.monitor_view.set_monitor_positions(self.monitor_positions)
        layout.addWidget(self.monitor_view, stretch=1)
        return content

    def _create_shortcuts_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Atajos de teclado")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)
        description = QLabel(
            "Configura una combinación o una secuencia de teclas para cada comando."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        self.shortcut_edits = {}
        for command, label in (("play", "Reproducir"), ("stop", "Detener")):
            edit = QKeySequenceEdit(QKeySequence(self.shortcuts.get(command, "")))
            edit.setClearButtonEnabled(True)
            self.shortcut_edits[command] = edit
            form.addRow(f"{label}:", edit)
        layout.addLayout(form)
        layout.addStretch()
        return page

    def _get_active_monitors(self) -> list[MonitorInfo]:
        return [
            monitor
            for monitor in self.monitors
            if self._checkboxes.get(monitor.name)
            and self._checkboxes[monitor.name].isChecked()
        ]

    def _active_monitors_changed(self) -> None:
        self.monitor_positions.update(self.monitor_view.monitor_positions())
        self.monitor_view.set_monitors(
            self._get_active_monitors(),
            self.monitor_positions,
        )

    def selected_monitor_names(self) -> set[str]:
        return {
            name
            for name, checkbox in self._checkboxes.items()
            if checkbox.isChecked()
        }

    def selected_monitor_positions(self) -> dict[str, QPointF]:
        return self.monitor_view.monitor_positions()

    def selected_shortcuts(self) -> dict[str, str]:
        return {
            command: edit.keySequence().toString(QKeySequence.SequenceFormat.NativeText)
            for command, edit in self.shortcut_edits.items()
        }
