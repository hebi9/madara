import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QGraphicsRectItem, QGraphicsScene

from app.sources.image_source import ImageSource
from app.ui.main_window import MainWindow
from app.ui.sources.source_item import SourceItem
from app.ui.widgets.monitor_layout_view import MonitorLayoutView


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_image_source_uses_real_dimensions(tmp_path, qapp):
    image_path = tmp_path / "sample.png"
    image = QImage(2, 3, QImage.Format_ARGB32)
    image.save(str(image_path))

    source = ImageSource.create(str(image_path))

    assert source.width == 2
    assert source.height == 3


def test_source_item_allows_position_outside_canvas(qapp):
    source = ImageSource(name="test", x=0, y=0, width=100, height=100)
    item = SourceItem(
        source=source,
        scale=1.0,
        canvas_width=200,
        canvas_height=200,
    )

    clamped = item._clamp_position(QPointF(300, 400))

    assert clamped.x() == 300
    assert clamped.y() == 400


def test_source_item_visibility_tracks_monitor_overlap(qapp):
    scene = QGraphicsScene()
    view = MonitorLayoutView(monitors=[])
    view.graphics_scene = scene

    monitor = QGraphicsRectItem(0, 0, 100, 100)
    monitor.setPos(0, 0)
    scene.addItem(monitor)
    view.monitor_items = [monitor]

    source = ImageSource(name="test", x=0, y=0, width=50, height=50)
    item = SourceItem(
        source=source,
        scale=1.0,
        canvas_width=100,
        canvas_height=100,
    )
    item.setPos(40, 40)
    scene.addItem(item)

    view.update_source_clip(item)
    assert item.isVisible()

    item.setPos(200, 200)
    view.update_source_clip(item)
    assert not item.isVisible()


def test_scenes_are_independent_of_selected_space(qapp):
    window = MainWindow()

    first_space = window._create_space()
    second_space = window._create_space()

    first_scene = window._create_scene(first_space)
    second_scene = window._create_scene(second_space)

    window._space_selected(first_space)

    displayed_names = [item.name for item in window.scenes_panel._items]

    # Las escenas son entidades globales (como en OBS): seleccionar
    # un espacio virtual no debe ocultar escenas de otros espacios.
    assert first_scene.name in displayed_names
    assert second_scene.name in displayed_names


def test_editing_selection_never_touches_program_scene(qapp):
    from app.models.project import SourceDefinition

    window = MainWindow()

    space = window._create_space()
    scene = window._create_scene()  # sin espacio: no debe activarse solo

    assert space.active_scene is None

    source = SourceDefinition(
        name="Texto 1",
        type="texto",
        x=0,
        y=0,
        width=100,
        height=100,
        text="hola",
    )
    scene.sources.append(source)

    # Simular navegación/edición del usuario: nada de esto debe
    # tocar la escena de Programa (salida en vivo).
    window._scene_selected(scene)
    window._source_selected(source)
    window._space_selected(space)
    window._scene_selected(scene)

    assert window.monitor_view.program_source_items == []
    assert space.active_scene is None

    # Solo la acción explícita "activar" pone la escena en vivo.
    window.activate_scene_for_space(space, scene)

    assert space.active_scene is scene
    assert len(window.monitor_view.program_source_items) == 1
    assert window.monitor_view.program_source_items[0].owner_space is space

    # Seguir editando/seleccionando NO debe alterar lo que ya está
    # en Programa.
    window._source_selected(source)
    window._space_selected(space)

    assert len(window.monitor_view.program_source_items) == 1
