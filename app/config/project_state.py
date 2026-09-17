from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.models.project import Scene, SourceDefinition, VirtualSpace


PROJECT_STATE_FILE = Path(__file__).resolve().parent / "project_state.json"


class ProjectState:
    """Persistencia local del estado de trabajo de Madara.

    Guarda únicamente datos del proyecto; no guarda QGraphicsItems,
    widgets ni objetos de Qt. La configuración física de monitores sigue
    siendo responsabilidad de MonitorConfig.
    """

    @staticmethod
    def load(path: Path = PROJECT_STATE_FILE) -> tuple[list[VirtualSpace], list[Scene]]:
        if not path.exists():
            return [], []

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError, TypeError):
            return [], []

        scenes: list[Scene] = []
        scene_by_id = {}

        for raw_scene in data.get("scenes", []):
            if not isinstance(raw_scene, dict):
                continue

            sources: list[SourceDefinition] = []
            for raw_source in raw_scene.get("sources", []):
                if not isinstance(raw_source, dict):
                    continue

                sources.append(
                    SourceDefinition(
                        name=str(raw_source.get("name", "Nueva fuente")),
                        type=str(raw_source.get("type", "texto")),
                        x=float(raw_source.get("x", 0)),
                        y=float(raw_source.get("y", 0)),
                        width=float(raw_source.get("width", 400)),
                        height=float(raw_source.get("height", 300)),
                        path=str(raw_source.get("path", "")),
                        url=str(raw_source.get("url", "")),
                        text=str(raw_source.get("text", "Nuevo texto")),
                        font_size=int(raw_source.get("font_size", 48)),
                        color=str(raw_source.get("color", "#FFFFFF")),
                    )
                )

            scene = Scene(
                name=str(raw_scene.get("name", "Nueva escena")),
                sources=sources,
            )
            scenes.append(scene)
            scene_id = raw_scene.get("id")
            if scene_id is not None:
                scene_by_id[str(scene_id)] = scene

        virtual_spaces: list[VirtualSpace] = []
        for raw_space in data.get("virtual_spaces", []):
            if not isinstance(raw_space, dict):
                continue

            active_scene = None
            active_scene_id = raw_space.get("active_scene_id")
            if active_scene_id is not None:
                active_scene = scene_by_id.get(str(active_scene_id))

            virtual_spaces.append(
                VirtualSpace(
                    name=str(raw_space.get("name", "Nuevo espacio")),
                    width=int(raw_space.get("width", 1920)),
                    height=int(raw_space.get("height", 1080)),
                    x=float(raw_space.get("x", 0)),
                    y=float(raw_space.get("y", 0)),
                    monitor_name=raw_space.get("monitor_name"),
                    active_scene=active_scene,
                )
            )

        return virtual_spaces, scenes

    @staticmethod
    def save(
        virtual_spaces: list[VirtualSpace],
        scenes: list[Scene],
        path: Path = PROJECT_STATE_FILE,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        scene_ids = {id(scene): str(index) for index, scene in enumerate(scenes)}

        payload = {
            "version": 1,
            "scenes": [
                {
                    "id": scene_ids[id(scene)],
                    "name": scene.name,
                    "sources": [asdict(source) for source in scene.sources],
                }
                for scene in scenes
            ],
            "virtual_spaces": [
                {
                    "name": space.name,
                    "width": space.width,
                    "height": space.height,
                    "x": space.x,
                    "y": space.y,
                    "monitor_name": space.monitor_name,
                    "active_scene_id": (
                        scene_ids.get(id(space.active_scene))
                        if space.active_scene is not None
                        else None
                    ),
                }
                for space in virtual_spaces
            ],
        }

        temporary_path = path.with_suffix(path.suffix + ".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4, ensure_ascii=False)

        temporary_path.replace(path)
