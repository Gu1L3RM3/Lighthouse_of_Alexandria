from pygame import Surface
from core.components.animation_sprite import AnimateSprite
from core.components.label_component import LabelComponent
from core.settings import *
from scenes.base_scene import BaseScene
from entities.dialogue_area import DialogueArea
from entities.animated_tiles.iron_gate import IronGate
from entities.itens.resistor_item import ResistorItem
from entities.itens.old_paper import OldPaper
from entities.animated_tiles.door import Door
from entities.itens.control_pannel import ControlPannel
from core.ui.widgets.fps_widget import FPSWidget
from core.ui.widgets.alert_dialog import AlertDialog
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.map.map_entity_spawner import MapEntitySpawner
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.resistor_pair_validator_system import ResistorPairValidatorSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.light_system import LightSystem
from core.managers.scene_manager import SceneManager
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
from core.circuit_tools.serialization_manager import SerializationManager
from core.managers.circuit_manager import CircuitManager
from utils.setter_values import SetterValues


class Level5(BaseScene):
    def __init__(self, screen: Surface):
        loader = TileMapLoader()
        self.level_path = 'fase_5'
        self.tile_map   = loader.load(f"fases/{self.level_path}.tmx")
        self.scale      = 2

        super().__init__(screen,
                         self.tile_map.map_width * self.scale,
                         self.tile_map.map_height * self.scale)

        self.camera.scale = self.scale

        self.map_renderer = MapRenderer(self.tile_map,
                                        self.camera,
                                        self.screen,
                                        self.scale)

        self.set_ui()
        self.set_map()
        self.set_systems()

        self.set_door()

        self.can_set_resistors = True

        self.player = self.entity_mn.get_player()
        self.camera.follow = self.player

        self.index_dialog_for_old_paper = '5'

        self.storage_circuit = StorageCircuitManager()

        self.scene_manager   = SceneManager.get()
        self.circuit_manager = CircuitManager.get()

    # ----------- Setup de cena / sistemas -----------

    def set_door(self):
        self.door: Door = self.entity_mn.get_entities_by_class(Door)[0]
        self.door.next_scene = 'level_2'

    def set_systems(self):
        self.animation_system         = AnimationSystem()
        self.area_trigger_system      = AreaTriggerSystem()
        self.freeze_system            = FreezeSystem()
        self.light_system             = LightSystem(self.screen,
                                                    self.camera,
                                                    debug=False,
                                                    enabled=True,
                                                    ambient_alpha=0)
        # aqui usamos o NOVO sistema
        self.circuit_validator_system = ResistorPairValidatorSystem(
            level_path=self.level_path,
            tolerance_percent=2.0
        )

        self.systems.update(
            [
                self.freeze_system,
                self.physics_system,
                self.animation_system,
                self.area_trigger_system,
                self.circuit_validator_system,
                self.render_system,
            ]
        )

    def set_ui(self):
        fps = FPSWidget()
        self.ui_manager.add(fps)

    def set_map(self):
        spawner = MapEntitySpawner()
        spawner.spawn_entities(self.tile_map, self.entity_mn)

        self.player = self.entity_mn.get_player()

        self.physics_system.cache_static_colliders(self.entity_mn)


    def start(self):
        self.scene_manager.scene_preview = 'level_5'
        self.clear_all_pannels_json()
        self.set_subscribes()
        self.set_resistors()

        self.old_paper: OldPaper = self.entity_mn.get_entities_by_class(OldPaper)[0]
        self.old_paper.on_active()

    def end(self):
        self.storage_circuit.remove_all_components()
        self.storage_circuit.save_eletric_storage()
        self.clear_all_pannels_json()

    def clear_all_pannels_json(self):
        amount_pannels = len(self.entity_mn.get_entities_by_class(ControlPannel))

        for i in range(amount_pannels):
            file_name = f'circuitos/{self.level_path}/pannel{i+1}.json'
            SerializationManager.remove_droppable_entities(file_name)
            SerializationManager.remove_resistor_by_name(file_name, "R3")



    def set_resistors(self):
        if not self.can_set_resistors:
            return

        self.can_set_resistors = False
        self.storage_circuit.remove_all_components()

        resistors_itens: list[ResistorItem] = self.entity_mn.get_entities_by_class(ResistorItem)
        amount = len(resistors_itens)
        resistor_values = self.circuit_manager.random_list_resistors(amount)

        for index, resistor_item in enumerate(resistors_itens):
            new_value = resistor_values[index]
            label: LabelComponent = resistor_item.get(LabelComponent)
            if label:
                label.value = new_value
            resistor_item.value = new_value

        resistors_per_area: dict[int, list[str]] = {}

        for resistor_item in resistors_itens:
            area_id = resistor_item.area_id
            if area_id not in resistors_per_area:
                resistors_per_area[area_id] = []
            resistors_per_area[area_id].append(resistor_item.value)

        self.event_manager.post({
            'type': 'set_solutions',
            'components': resistors_per_area
        })


    def set_subscribes(self):
        self.event_manager.subscribe(
            'set_solutions',
            lambda event: self.circuit_validator_system.set_solutions(event, self.entity_mn)
        )
        self.event_manager.subscribe('solutions_done', self.set_dialogue)
        self.event_manager.subscribe('fall_player', self.fall_player)
        self.event_manager.subscribe('request_freeze', self.freeze_system.request_freeze)
        self.event_manager.subscribe('release_freeze', self.freeze_system.release_freeze)
        self.event_manager.subscribe('set_cache_colliders',
                                     lambda event: self.physics_system.cache_static_colliders(self.entity_mn))
        self.event_manager.subscribe("kill_entity", self.kill_entity_event)
        self.event_manager.subscribe("resistor_collected", self.update_storage_circuit)
        self.event_manager.subscribe("open_old_paper", self.open_old_paper)
        self.event_manager.subscribe("close_old_paper", self.after_close_old_paper)
        self.event_manager.subscribe("pannel_luz1", lambda event: self.light_system.toggle)
        self.event_manager.subscribe("pannel_door3", self.door.open)
        self.subscribe_iron_gates()

    def subscribe_iron_gates(self):
        irons_gates: list[IronGate] = self.entity_mn.get_entities_by_class(IronGate)

        for iron_gate in irons_gates:
            self.event_manager.subscribe(f'pannel_iron_gate{iron_gate.pannel_id}', iron_gate.open)


    def set_dialogue(self, event):
        text_list = []
        pannels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
        dialogue_area: DialogueArea = self.entity_mn.get_entities_by_class(DialogueArea)[0]

        for pannel in pannels:
            solution_type = pannel.solution_type
            solution_value = pannel.solution_value

            if not solution_type or not solution_value:
                continue

            if solution_type == "voltage":
                parts = [
                    f"{r_name} ≈ {SetterValues.format_eng(val, 'V')}"
                    for r_name, val in solution_value.items()
                ]
                joined = ", ".join(parts)
                text_list.append(
                    f"Arquimedes: Para ativar o painel {pannel.pannel_id}, as tensões devem ser aproximadamente: {joined}"
                )

            elif solution_type == "current":
                parts = [
                    f"{r_name} ≈ {SetterValues.format_eng(val, 'A')}"
                    for r_name, val in solution_value.items()
                ]
                joined = ", ".join(parts)
                text_list.append(
                    f"Arquimedes: Para ativar o painel {pannel.pannel_id}, as correntes devem ser aproximadamente: {joined}"
                )

        if text_list:
            dialogue_area.add_dialogue_text(text_list)


    def set_old_paper(self, event):
        dialogue: DialogueArea = event['entity']
        if not isinstance(dialogue, DialogueArea):
            return
        if self.index_dialog_for_old_paper not in dialogue.name:
            return

        self.old_paper: OldPaper = self.entity_mn.get_entities_by_class(OldPaper)[0]
        self.old_paper.on_active()

    def after_close_old_paper(self, event):
        self.event_manager.post({'type': 'release_freeze'})

    def open_old_paper(self, event):
        self.event_manager.post({'type': 'request_freeze', 'type_request': 'open paper'})

        def close_old_paper(widget):
            self.ui_manager.remove(widget)
            self.event_manager.post({'type': 'close_old_paper'})

        paper: Surface = self.resources.load_image('letters/letter_3.png')
        alert_dialog = AlertDialog(
            title='',
            surface=paper,
            on_close=close_old_paper
        )
        self.ui_manager.add(alert_dialog)


    def fall_player(self, event):
        self.can_set_resistors = True
        anim: AnimateSprite = self.player.get(AnimateSprite)
        anim.play('fall', loop=False, on_finish=self.scene_manager.restart_with_fade)

    def update_storage_circuit(self, event):
        value = event['value']
        self.storage_circuit.reload_storage()
        self.storage_circuit.add_component(type='Resistor', value=value)
        self.storage_circuit.save_eletric_storage()

    def kill_entity_event(self, event):
        self.entity_mn.remove_entity_by_id(event['id'])


    def process_input(self, events):
        self.player.input(events)

    def update(self, dt):
        self.dialog_system.update(self.entity_mn, self.player, dt)
        self.update_systems(dt)
        self.ui_manager.update(dt)

    def render(self):
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale)
        self.light_system.update(self.entity_mn, 0)
        self.ui_manager.draw(self.screen)
