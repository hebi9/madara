from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QPushButton,
)


class PropertiesPanel(QWidget):

    object_changed = Signal(object)

    def __init__(
        self,
        parent=None,
    ) -> None:

        super().__init__(
            parent
        )

        self.current_object = None

        self.monitors = []

        self.spaces = []

        self.active_monitor_names = set()

        self.setMinimumWidth(
            280
        )

        self._setup_ui()

    # ==========================================================
    # CONTEXTO
    # ==========================================================

    def set_context(
        self,
        monitors,
        spaces,
        active_monitor_names,
    ) -> None:

        self.monitors = list(
            monitors
        )

        self.spaces = list(
            spaces
        )

        self.active_monitor_names = set(
            active_monitor_names
        )

        if self.current_object is not None:

            self.set_object(
                self.current_object
            )

    # ==========================================================
    # UI
    # ==========================================================

    def _setup_ui(self) -> None:

        self.layout = QVBoxLayout(
            self
        )

        self.layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        self.title = QLabel(
            "Propiedades"
        )

        self.title.setStyleSheet(
            "font-weight: bold;"
        )

        self.layout.addWidget(
            self.title
        )

        self.form_container = QWidget()

        self.form_layout = QFormLayout(
            self.form_container
        )

        self.layout.addWidget(
            self.form_container
        )

        self.layout.addStretch()

        self._show_empty()

    # ==========================================================
    # FORMULARIO
    # ==========================================================

    def _clear_form(self) -> None:

        while self.form_layout.count():

            item = (
                self.form_layout.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

    def _show_empty(self) -> None:

        self._clear_form()

        self.title.setText(
            "Propiedades"
        )

        label = QLabel(
            "Selecciona un elemento."
        )

        label.setWordWrap(
            True
        )

        self.form_layout.addRow(
            label
        )

    def set_object(
        self,
        obj,
    ) -> None:

        self.current_object = obj

        if obj is None:

            self._show_empty()

            return

        self._clear_form()

        object_type = type(
            obj
        ).__name__

        self.title.setText(
            f"Propiedades: {object_type}"
        )

        self.name_edit = QLineEdit(
            str(
                getattr(
                    obj,
                    "name",
                    "",
                )
            )
        )

        self.name_edit.editingFinished.connect(
            self._name_changed
        )

        self.form_layout.addRow(
            "Nombre:",
            self.name_edit,
        )

        # ======================================================
        # ESPACIO VIRTUAL
        # ======================================================

        if hasattr(
            obj,
            "monitor_name",
        ):

            self.width_spin = self._spin(
                getattr(
                    obj,
                    "width",
                    1920,
                ),
                1,
                100000,
            )

            self.height_spin = self._spin(
                getattr(
                    obj,
                    "height",
                    1080,
                ),
                1,
                100000,
            )

            self.width_spin.valueChanged.connect(
                self._space_size_changed
            )

            self.height_spin.valueChanged.connect(
                self._space_size_changed
            )

            self.form_layout.addRow(
                "Ancho:",
                self.width_spin,
            )

            self.form_layout.addRow(
                "Alto:",
                self.height_spin,
            )

            self.monitor_combo = QComboBox()

            self._populate_monitor_combo(
                obj
            )

            self.monitor_combo.currentIndexChanged.connect(
                self._monitor_changed
            )

            self.form_layout.addRow(
                "Monitor:",
                self.monitor_combo,
            )

            return

        # ======================================================
        # FUENTE
        # ======================================================

        if hasattr(
            obj,
            "type",
        ):

            self.type_combo = QComboBox()

            self.type_combo.addItem(
                "Texto",
                "texto",
            )

            self.type_combo.addItem(
                "Imagen",
                "imagen",
            )

            self.type_combo.addItem(
                "Video",
                "video",
            )

            self.type_combo.addItem(
                "Internet (URL)",
                "url",
            )

            index = self.type_combo.findData(
                obj.type
            )

            if index >= 0:

                self.type_combo.setCurrentIndex(
                    index
                )

            self.type_combo.currentIndexChanged.connect(
                self._type_changed
            )

            self.form_layout.addRow(
                "Tipo:",
                self.type_combo,
            )

            self.x_spin = self._spin(
                obj.x,
                -100000,
                100000,
            )

            self.y_spin = self._spin(
                obj.y,
                -100000,
                100000,
            )

            self.width_spin = self._spin(
                obj.width,
                1,
                100000,
            )

            self.height_spin = self._spin(
                obj.height,
                1,
                100000,
            )

            self.x_spin.valueChanged.connect(
                self._source_geometry_changed
            )

            self.y_spin.valueChanged.connect(
                self._source_geometry_changed
            )

            self.width_spin.valueChanged.connect(
                self._source_geometry_changed
            )

            self.height_spin.valueChanged.connect(
                self._source_geometry_changed
            )

            self.form_layout.addRow(
                "X:",
                self.x_spin,
            )

            self.form_layout.addRow(
                "Y:",
                self.y_spin,
            )

            self.form_layout.addRow(
                "Ancho:",
                self.width_spin,
            )

            self.form_layout.addRow(
                "Alto:",
                self.height_spin,
            )

            if obj.type == "texto":

                self.text_edit = QLineEdit(
                    obj.text
                )

                self.text_edit.editingFinished.connect(
                    self._text_changed
                )

                self.form_layout.addRow(
                    "Texto:",
                    self.text_edit,
                )

            elif obj.type == "imagen":

                self.path_edit = QLineEdit(
                    obj.path
                )

                self.path_edit.setReadOnly(
                    True
                )

                self.path_button = QPushButton(
                    "Examinar..."
                )

                self.path_button.clicked.connect(
                    self._select_image
                )

                path_layout = QHBoxLayout()

                path_layout.addWidget(
                    self.path_edit
                )

                path_layout.addWidget(
                    self.path_button
                )

                path_widget = QWidget()

                path_widget.setLayout(
                    path_layout
                )

                self.form_layout.addRow(
                    "Archivo:",
                    path_widget,
                )

            elif obj.type == "video":

                self.path_edit = QLineEdit(obj.path)
                self.path_edit.setReadOnly(True)
                self.path_button = QPushButton("Examinar...")
                self.path_button.clicked.connect(self._select_video)
                path_layout = QHBoxLayout()
                path_layout.addWidget(self.path_edit)
                path_layout.addWidget(self.path_button)
                path_widget = QWidget()
                path_widget.setLayout(path_layout)
                self.form_layout.addRow("Video:", path_widget)

            elif obj.type == "url":

                self.url_edit = QLineEdit(obj.url)
                self.url_edit.setPlaceholderText("https://...")
                self.url_edit.editingFinished.connect(self._url_changed)
                self.form_layout.addRow("URL:", self.url_edit)
    def _select_image(self) -> None:

        if self.current_object is None:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.webp)",
        )

        if not path:
            return

        self.current_object.path = path

        self.path_edit.setText(
            path
        )

        self.object_changed.emit(
            self.current_object
        )

    def _select_video(self) -> None:
        if self.current_object is None:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar video",
            "",
            "Videos (*.mp4 *.mov *.avi *.mkv *.webm *.m4v)",
        )
        if not path:
            return

        self.current_object.path = path
        self.path_edit.setText(path)
        self.object_changed.emit(self.current_object)

    def _url_changed(self) -> None:
        if self.current_object is None or not hasattr(self, "url_edit"):
            return

        url = self.url_edit.text().strip()
        if not url:
            return

        self.current_object.url = url
        self.object_changed.emit(self.current_object)

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _spin(
        self,
        value,
        minimum,
        maximum,
    ):

        spin = QSpinBox()

        spin.setRange(
            minimum,
            maximum,
        )

        spin.setValue(
            int(value)
        )

        return spin

    # ==========================================================
    # MONITORES
    # ==========================================================

    def _populate_monitor_combo(
        self,
        space,
    ) -> None:

        self.monitor_combo.blockSignals(
            True
        )

        self.monitor_combo.clear()

        self.monitor_combo.addItem(
            "Sin asignar",
            None,
        )

        assigned_to_other = {
            other.monitor_name
            for other in self.spaces
            if other is not space
            and other.monitor_name
        }

        for monitor in self.monitors:

            if (
                monitor.name
                not in self.active_monitor_names
            ):
                continue

            if (
                monitor.name
                in assigned_to_other
            ):
                continue

            geometry = monitor.geometry

            text = (
                f"{monitor.name}  •  "
                f"{geometry.width()} × "
                f"{geometry.height()}"
            )

            self.monitor_combo.addItem(
                text,
                monitor.name,
            )

        index = self.monitor_combo.findData(
            space.monitor_name
        )

        if index < 0:

            index = 0

        self.monitor_combo.setCurrentIndex(
            index
        )

        self.monitor_combo.blockSignals(
            False
        )

    def _monitor_changed(
        self,
        index: int,
    ) -> None:

        if self.current_object is None:
            return

        if not hasattr(
            self.current_object,
            "monitor_name",
        ):
            return

        self.current_object.monitor_name = (
            self.monitor_combo.currentData()
        )

        self.object_changed.emit(
            self.current_object
        )

    # ==========================================================
    # ESPACIO
    # ==========================================================

    def _space_size_changed(
        self,
    ) -> None:

        if self.current_object is None:
            return

        self.current_object.width = (
            self.width_spin.value()
        )

        self.current_object.height = (
            self.height_spin.value()
        )

        self.object_changed.emit(
            self.current_object
        )

    # ==========================================================
    # FUENTE
    # ==========================================================

    def _source_geometry_changed(
        self,
    ) -> None:

        if self.current_object is None:
            return

        self.current_object.x = (
            self.x_spin.value()
        )

        self.current_object.y = (
            self.y_spin.value()
        )

        self.current_object.width = (
            self.width_spin.value()
        )

        self.current_object.height = (
            self.height_spin.value()
        )

        self.object_changed.emit(
            self.current_object
        )

    def _type_changed(
        self,
        index: int,
    ) -> None:

        if self.current_object is None:
            return

        self.current_object.type = (
            self.type_combo.currentData()
        )

        self.object_changed.emit(
            self.current_object
        )

        self.set_object(
            self.current_object
        )

    def _text_changed(
        self,
    ) -> None:

        if self.current_object is None:
            return

        if not hasattr(
            self.current_object,
            "text",
        ):
            return

        self.current_object.text = (
            self.text_edit.text()
        )

        self.object_changed.emit(
            self.current_object
        )

    def _name_changed(
        self,
    ) -> None:

        if self.current_object is None:
            return

        if not hasattr(
            self.current_object,
            "name",
        ):
            return

        self.current_object.name = (
            self.name_edit.text()
        )

        self.object_changed.emit(
            self.current_object
        )