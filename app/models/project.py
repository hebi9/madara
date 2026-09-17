from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SourceDefinition:
    name: str
    type: str = "texto"
    x: float = 0
    y: float = 0
    width: float = 400
    height: float = 300
    path: str = ""
    url: str = ""
    text: str = "Nuevo texto"
    font_size: int = 48
    color: str = "#FFFFFF"


@dataclass
class Scene:
    # Las escenas son entidades independientes (como en OBS): no
    # pertenecen a ningún espacio virtual. Un espacio virtual solo
    # delimita el lienzo y referencia la escena que debe renderizar
    # mediante `VirtualSpace.active_scene`.
    name: str
    sources: list[SourceDefinition] = field(default_factory=list)


@dataclass
class VirtualSpace:
    name: str
    width: int = 1920
    height: int = 1080
    x: float = 0
    y: float = 0
    monitor_name: str | None = None
    active_scene: Scene | None = None