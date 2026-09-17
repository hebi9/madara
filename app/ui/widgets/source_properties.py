from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.sources.text_source import TextSource
from app.ui.sources.source_item import SourceItem


class SourceProperties(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.source_item: SourceItem | None = None

        self.setFixedWidth(280)

        layout = QVBoxLayout(self)

        title = QLabel(
            "Propiedades de fuente"
        )

        title.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )

        layout.addWidget(title)

        self.form = QFormLayout()

        self.name_edit = QLineEdit()

        self.x_spin = QSpinBox()
        self.y_spin = QSpinBox()

        self.width_spin = QSpinBox()
        self.height_spin = QSpinBox()

        for spin in (
            self.x_spin,
            self.y_spin,
            self.width_spin,
            self.height_spin,
        ):
            spin.setRange(
                0,
                10000,
            )

        self.form.addRow(
            "Nombre:",
            self.name_edit,
        )

        self.form.addRow(
            "X:",
            self.x_spin,
        )

        self.form.addRow(
            "Y:",
            self.y_spin,
        )

        self.form.addRow(
            "Ancho:",
            self.width_spin,
        )

        self.form.addRow(
            "Alto:",
            self.height_spin,
        )

        layout.addLayout(
            self.form
        )

        self.text_group = QGroupBox(
            "Texto"
        )

        text_layout = QVBoxLayout(
            self.text_group
        )

        self.text_edit = QTextEdit()

        self.text_edit.setFixedHeight(
            100
        )

        text_layout.addWidget(
            self.text_edit
        )

        self.font_size_spin = QSpinBox()

        self.font_size_spin.setRange(
            1,
            500,
        )

        text_layout.addWidget(
            QLabel("Tamaño de fuente:")
        )

        text_layout.addWidget(
            self.font_size_spin
        )

        self.color_button = QPushButton(
            "Color del texto"
        )

        text_layout.addWidget(
            self.color_button
        )

        layout.addWidget(
            self.text_group
        )

        layout.addStretch()

        self.name_edit.editingFinished.connect(
            self._name_changed
        )

        self.x_spin.valueChanged.connect(
            self._position_changed
        )

        self.y_spin.valueChanged.connect(
            self._position_changed
        )

        self.width_spin.valueChanged.connect(
            self._size_changed
        )

        self.height_spin.valueChanged.connect(
            self._size_changed
        )

        self.text_edit.textChanged.connect(
            self._text_changed
        )

        self.font_size_spin.valueChanged.connect(
            self._font_size_changed
        )

        self.color_button.clicked.connect(
            self._choose_color
        )

        self.clear()

    def set_source(
        self,
        source_item: SourceItem | None,
    ) -> None:

        self.source_item = source_item

        self._block_form_signals(True)

        if source_item is None:

            self.name_edit.clear()
            self.x_spin.setValue(0)
            self.y_spin.setValue(0)
            self.width_spin.setValue(0)
            self.height_spin.setValue(0)

            self.text_group.setVisible(False)

            self._block_form_signals(False)
            self._set_enabled(False)
            return

        source = source_item.source

        self.name_edit.setText(source.name)
        self.x_spin.setValue(round(source.x))
        self.y_spin.setValue(round(source.y))
        self.width_spin.setValue(round(source.width))
        self.height_spin.setValue(round(source.height))

        is_text = isinstance(source, TextSource)

        self.text_group.setVisible(is_text)

        if is_text:
            self.text_edit.setPlainText(source.text)
            self.font_size_spin.setValue(source.font_size)
            self._update_color_button(source.color)

        self._block_form_signals(False)
        self._set_enabled(True)

    def clear(self) -> None:

        self.source_item = None

        self.name_edit.clear()

        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
        self.width_spin.setValue(0)
        self.height_spin.setValue(0)

        self.text_edit.clear()

        self.text_group.setVisible(
            False
        )

        self._set_enabled(False)

    def _set_enabled(
        self,
        enabled: bool,
    ) -> None:

        self.name_edit.setEnabled(
            enabled
        )

        self.x_spin.setEnabled(
            enabled
        )

        self.y_spin.setEnabled(
            enabled
        )

        self.width_spin.setEnabled(
            enabled
        )

        self.height_spin.setEnabled(
            enabled
        )

    def _name_changed(self) -> None:

        if self.source_item is None:
            return

        self.source_item.source.name = (
            self.name_edit.text()
        )

    def _position_changed(self) -> None:

        if self.source_item is None:
            return

        self.source_item.set_source_position(
            self.x_spin.value(),
            self.y_spin.value(),
        )

    def _size_changed(self) -> None:

        if self.source_item is None:
            return

        self.source_item.set_source_size(
            self.width_spin.value(),
            self.height_spin.value(),
        )

    def _text_changed(self) -> None:

        if self.source_item is None:
            return

        if not isinstance(
            self.source_item.source,
            TextSource,
        ):
            return

        self.source_item.source.text = (
            self.text_edit.toPlainText()
        )

        self.source_item.update_visual()

    def _font_size_changed(
        self,
        value: int,
    ) -> None:

        if self.source_item is None:
            return

        if not isinstance(
            self.source_item.source,
            TextSource,
        ):
            return

        self.source_item.source.font_size = (
            value
        )

        self.source_item.update_visual()

    def _choose_color(self) -> None:

        if self.source_item is None:
            return

        if not isinstance(
            self.source_item.source,
            TextSource,
        ):
            return

        current = QColor(
            self.source_item.source.color
        )

        color = QColorDialog.getColor(
            current,
            self,
            "Seleccionar color",
        )

        if not color.isValid():
            return

        self.source_item.source.color = (
            color.name()
        )

        self._update_color_button(
            color.name()
        )

        self.source_item.update_visual()

    def _update_color_button(
        self,
        color: str,
    ) -> None:

        self.color_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: black;
                border: 1px solid #555;
            }}
            """
        )

    def _block_form_signals(
        self,
        blocked: bool,
    ):

        for widget in (
            self.name_edit,
            self.x_spin,
            self.y_spin,
            self.width_spin,
            self.height_spin,
            self.text_edit,
            self.font_size_spin,
        ):
            widget.blockSignals(blocked)