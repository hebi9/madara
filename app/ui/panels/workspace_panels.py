from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class EntityListPanel(QWidget):

    item_selected = Signal(object)
    item_created = Signal()
    item_deleted = Signal(object)
    item_renamed = Signal(object, str)
    items_reordered = Signal(list)

    def __init__(
        self,
        title: str,
        parent=None,
        reorderable: bool = False,
    ) -> None:

        super().__init__(parent)

        self.title = title
        self.reorderable = reorderable
        self._items: list[object] = []
        self._display_function = lambda item: str(item)

        self._setup_ui()

    def _setup_ui(self) -> None:

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(5)

        title_layout = QHBoxLayout()

        title_label = QLabel(
            self.title
        )

        title_layout.addWidget(
            title_label
        )

        title_layout.addStretch()

        self.add_button = QPushButton("+")
        self.add_button.setFixedWidth(28)

        self.add_button.clicked.connect(
            self.item_created.emit
        )

        title_layout.addWidget(
            self.add_button
        )

        layout.addLayout(
            title_layout
        )

        self.list_widget = QListWidget()

        if self.reorderable:
            self.list_widget.setDragDropMode(
                QListWidget.DragDropMode.InternalMove
            )
            self.list_widget.setDefaultDropAction(
                Qt.DropAction.MoveAction
            )
            self.list_widget.model().rowsMoved.connect(
                self._rows_moved
            )

        self.list_widget.itemSelectionChanged.connect(
            self._selection_changed
        )

        self.list_widget.itemClicked.connect(
            self._selection_changed
        )

        self.list_widget.itemDoubleClicked.connect(
            self._rename_item
        )

        layout.addWidget(
            self.list_widget,
            stretch=1,
        )

        self.delete_button = QPushButton(
            "Eliminar"
        )

        self.delete_button.setEnabled(
            False
        )

        self.delete_button.clicked.connect(
            self._delete_selected
        )

        layout.addWidget(
            self.delete_button
        )

    def set_items(
        self,
        items: list[object],
        display_function,
    ) -> None:

        self._items = list(items)
        self._display_function = display_function

        self.list_widget.blockSignals(
            True
        )

        self.list_widget.clear()

        for index, item in enumerate(
            self._items
        ):

            list_item = QListWidgetItem(
                display_function(item)
            )

            list_item.setData(
                Qt.ItemDataRole.UserRole,
                index,
            )

            self.list_widget.addItem(
                list_item
            )

        self.list_widget.blockSignals(
            False
        )

        self._update_buttons()

    def _sync_items_from_list(self) -> None:
        reordered: list[object] = []

        for row in range(self.list_widget.count()):
            list_item = self.list_widget.item(row)
            index = list_item.data(Qt.ItemDataRole.UserRole)

            if isinstance(index, int) and 0 <= index < len(self._items):
                reordered.append(self._items[index])

        if len(reordered) == len(self._items):
            self._items = reordered

        for row in range(self.list_widget.count()):
            self.list_widget.item(row).setData(
                Qt.ItemDataRole.UserRole,
                row,
            )

    def _rows_moved(self, parent, start, end, destination, row) -> None:
        if not self.reorderable:
            return

        self._sync_items_from_list()
        self.items_reordered.emit(list(self._items))

    def _selection_changed(self) -> None:

        selected = (
            self.list_widget.selectedItems()
        )

        if not selected:
            self.delete_button.setEnabled(
                False
            )
            return

        index = selected[0].data(
            Qt.ItemDataRole.UserRole
        )

        if index is None:
            return

        self.delete_button.setEnabled(
            True
        )

        if index >= len(self._items):
            return

        self.item_selected.emit(
            self._items[index]
        )

    def _delete_selected(self) -> None:

        selected = (
            self.list_widget.selectedItems()
        )

        if not selected:
            return

        index = selected[0].data(
            Qt.ItemDataRole.UserRole
        )

        if index is None or index >= len(self._items):
            return

        self.item_deleted.emit(
            self._items[index]
        )

    def _rename_item(
        self,
        item: QListWidgetItem,
    ) -> None:

        index = item.data(
            Qt.ItemDataRole.UserRole
        )

        if index is None or index >= len(self._items):
            return

        entity = self._items[index]

        self.list_widget.editItem(
            item
        )

        self.item_renamed.emit(
            entity,
            item.text(),
        )

    def _update_buttons(self) -> None:

        self.delete_button.setEnabled(
            bool(
                self.list_widget.selectedItems()
            )
        )

    def selected_entity(self):

        selected = (
            self.list_widget.selectedItems()
        )

        if not selected:
            return None

        index = selected[0].data(
            Qt.ItemDataRole.UserRole
        )

        if index is None or index >= len(self._items):
            return None

        return self._items[index]
