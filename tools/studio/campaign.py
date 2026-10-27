"""The game's level sequence, as the door `next_scene` properties of each map describe it.

Every .tmx in a stage folder is registered by `Game.register_fases()` with that stage's scene class,
so an extra level dropped into a stage folder reuses the stage's validator. Placing it in the
sequence only means rewiring doors.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from studio.tmx_io import TmxDocument


class CampaignError(ValueError):
    pass


@dataclass(frozen=True)
class Stage:
    number: int
    folder: str
    title: str
    answer_types: tuple[str, ...]


STAGES = (
    Stage(3, "generic_levels_3", "Lei de Ohm", ("voltage", "current", "power")),
    Stage(4, "generic_levels_4", "Associação de resistores", ("resistance",)),
    Stage(5, "generic_levels_5", "Par de resistores", ("voltage", "current")),
    Stage(6, "generic_levels_6", "Thévenin e Norton", ("voltage;current",)),
    Stage(7, "generic_levels_7", "Máxima transferência de potência", ("power;resistance", "power", "resistance", "voltage", "current")),
    Stage(8, "final_fase", "Fase final", ("power;resistance", "power", "resistance", "voltage", "current")),
)
STAGE_BY_FOLDER = {stage.folder: stage for stage in STAGES}
ORIGINAL_LEVELS = frozenset({"fase_3", "fase_4", "fase_5", "fase_6", "fase_7", "fase_8"})

START_SCENE = "level_1"
# Hand-written scenes set their next scene in code, so their maps' doors are ignored by the game.
CODE_TRANSITIONS = {
    "level_1": "level_2",
    "level_2": "exp_fase_3",
    "exp_fase_3": "fase_3",
    "exp_fase_4": "fase_4",
    "exp_fase_5": "fase_5",
    "exp_fase_6": "fase_6",
    "exp_fase_7": "fase_7",
}
CODE_SCENES = frozenset({
    "main_menu", "credits", "help", "ending_lighthouse", "ending_thanks_credits", "home_scene",
    "home_after", "death_transition", "level_1", "level_2", "circuit_editor_boot",
    *CODE_TRANSITIONS,
})
SCENE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,40}$")
DOOR_LAYER = "door"
BLANK_LEVEL_KEEPS = frozenset({"door", "player"})
NEXT_SCENE = "next_scene"


class Campaign:
    def __init__(self, maps_dir: Path, circuits_dir: Path):
        self.maps_dir = Path(maps_dir)
        self.circuits_dir = Path(circuits_dir)

    # reading ------------------------------------------------------------

    def stage_levels(self) -> dict[str, Stage]:
        """Scene name -> stage, for every map inside a stage folder."""
        levels = {}
        for stage in STAGES:
            for tmx in sorted((self.maps_dir / stage.folder).glob("*.tmx")):
                levels[tmx.stem] = stage
        return levels

    def tmx_path(self, scene: str) -> Path:
        stage = self.stage_levels().get(scene)
        if stage is None:
            raise CampaignError(f"{scene} não é uma fase editável")
        return self.maps_dir / stage.folder / f"{scene}.tmx"

    def level_path(self, scene: str) -> str:
        """The `level_path` the game passes to the scene, e.g. generic_levels_4/fase_4."""
        return f"{self.tmx_path(scene).parent.name}/{scene}"

    def next_of(self, scene: str) -> str | None:
        if scene in CODE_TRANSITIONS:
            return CODE_TRANSITIONS[scene]
        if scene not in self.stage_levels():
            return None
        return self._door_target(self.tmx_path(scene))

    def chain(self) -> list[dict]:
        levels = self.stage_levels()
        steps, seen, scene = [], set(), START_SCENE
        while scene and scene not in seen:
            seen.add(scene)
            stage = levels.get(scene)
            steps.append({
                "scene": scene,
                "stage": stage.number if stage else None,
                "editable": stage is not None,
                "original": scene in ORIGINAL_LEVELS or stage is None,
                "next": self.next_of(scene),
            })
            scene = steps[-1]["next"]
        return steps

    def stages(self) -> list[dict]:
        order = [step["scene"] for step in self.chain()]
        levels = self.stage_levels()
        return [
            {
                "number": stage.number,
                "folder": stage.folder,
                "title": stage.title,
                "answer_types": list(stage.answer_types),
                "levels": [scene for scene in order if levels.get(scene) == stage],
            }
            for stage in STAGES
        ]

    def issues(self) -> list[str]:
        chain = self.chain()
        reached = {step["scene"] for step in chain}
        problems = [
            f"A fase {scene} está na pasta da etapa {stage.number}, mas nenhuma porta leva até ela."
            for scene, stage in self.stage_levels().items()
            if scene not in reached
        ]
        last = chain[-1]
        if last["next"] and last["next"] in reached:
            problems.append(f"A porta de {last['scene']} volta para {last['next']} e cria um ciclo.")
        elif last["next"]:
            problems.append(f"A porta de {last['scene']} leva a {last['next']}, que não existe.")
        return problems

    def suggest_name(self, stage_number: int) -> str:
        taken = self._all_scene_names()
        index = 2
        while f"fase_{stage_number}_{index}" in taken:
            index += 1
        return f"fase_{stage_number}_{index}"

    # editing ------------------------------------------------------------

    def insert_after(self, scene: str, new_scene: str, template: str | None = None, blank: bool = False) -> None:
        stage = self._stage_of_editable(scene)
        self._check_new_name(new_scene)
        template = template or scene
        if self.stage_levels().get(template) != stage:
            raise CampaignError(f"O modelo {template} precisa ser da etapa {stage.number}")
        following = self._door_target(self.tmx_path(scene))
        if following is None:
            raise CampaignError(f"{scene} termina o jogo; insira a fase antes dela")

        target_tmx = self.maps_dir / stage.folder / f"{new_scene}.tmx"
        shutil.copy(self.tmx_path(template), target_tmx)
        template_circuits = self.circuits_dir / stage.folder / template
        if blank:
            self._clear_map(target_tmx)
        elif template_circuits.exists():
            shutil.copytree(template_circuits, self.circuits_dir / stage.folder / new_scene)
        self._set_door_target(target_tmx, following)
        self._set_door_target(self.tmx_path(scene), new_scene)

    def remove(self, scene: str) -> None:
        if scene in ORIGINAL_LEVELS:
            raise CampaignError(f"{scene} é uma fase original do jogo e não pode ser removida")
        stage = self._stage_of_editable(scene)
        self._unlink(scene)
        self.tmx_path(scene).unlink()
        shutil.rmtree(self.circuits_dir / stage.folder / scene, ignore_errors=True)

    def move(self, scene: str, after: str) -> None:
        if scene in ORIGINAL_LEVELS:
            raise CampaignError(f"{scene} é uma fase original do jogo e não pode mudar de lugar")
        stage = self._stage_of_editable(scene)
        if self.stage_levels().get(after) != stage or after == scene:
            raise CampaignError(f"{scene} só pode ir para depois de outra fase da etapa {stage.number}")
        self._unlink(scene)
        following = self._door_target(self.tmx_path(after))
        self._set_door_target(self.tmx_path(scene), following)
        self._set_door_target(self.tmx_path(after), scene)

    # helpers ------------------------------------------------------------

    def _stage_of_editable(self, scene: str) -> Stage:
        stage = self.stage_levels().get(scene)
        if stage is None:
            raise CampaignError(f"{scene} não é uma fase editável")
        return stage

    def _unlink(self, scene: str) -> None:
        previous = next((step["scene"] for step in self.chain() if step["next"] == scene), None)
        if previous is None or previous not in self.stage_levels():
            raise CampaignError(f"Não achei a fase anterior a {scene}")
        self._set_door_target(self.tmx_path(previous), self._door_target(self.tmx_path(scene)))

    def _check_new_name(self, name: str) -> None:
        if not SCENE_NAME.match(name):
            raise CampaignError("Use só letras minúsculas, números e _ no nome da fase (ex.: fase_4_2)")
        if name in self._all_scene_names():
            raise CampaignError(f"Já existe uma cena chamada {name}")

    def _all_scene_names(self) -> set[str]:
        return {tmx.stem for tmx in self.maps_dir.rglob("*.tmx")} | CODE_SCENES

    @staticmethod
    def _clear_map(tmx: Path) -> None:
        """Blank canvas with the template's size and tilesets; only the door and the player's start stay."""
        document = TmxDocument(tmx)
        data = document.to_dict()
        for layer in data["layers"]:
            layer["data"] = [0] * len(layer["data"])
        for group in data["objectgroups"]:
            group["objects"] = [obj for obj in group["objects"] if obj.get("name") in BLANK_LEVEL_KEEPS]
        document.update(data)
        document.save()

    @staticmethod
    def _door_target(tmx: Path) -> str | None:
        for group in TmxDocument(tmx).to_dict()["objectgroups"]:
            if group["name"] != DOOR_LAYER:
                continue
            for obj in group["objects"]:
                for prop in obj["properties"]:
                    if prop["name"] == NEXT_SCENE and prop["value"]:
                        return prop["value"]
        return None

    @staticmethod
    def _set_door_target(tmx: Path, target: str) -> None:
        document = TmxDocument(tmx)
        data = document.to_dict()
        doors = [group for group in data["objectgroups"] if group["name"] == DOOR_LAYER]
        if not doors or not doors[0]["objects"]:
            raise CampaignError(f"{tmx.stem} não tem porta; coloque uma porta no mapa antes")
        for obj in doors[0]["objects"]:
            others = [prop for prop in obj["properties"] if prop["name"] != NEXT_SCENE]
            obj["properties"] = [*others, {"name": NEXT_SCENE, "type": "string", "value": target}]
        document.update({"objectgroups": doors})
        document.save()
