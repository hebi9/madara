from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class BaseSource:
    name: str
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 100
    id: str = field(default_factory=lambda: str(uuid4()))
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0