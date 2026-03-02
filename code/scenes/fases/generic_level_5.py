from pygame import Surface
from core.settings import *
from entities.dialogue_area import DialogueArea
from entities.itens.old_paper import OldPaper
from entities.itens.control_pannel import ControlPannel
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.resistor_pair_validator_system import ResistorPairValidatorSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.light_system import LightSystem
from core.circuit_tools.serialization_manager import SerializationManager
from utils.setter_values import SetterValues
from pathlib import Path
from scenes.fases.generic_levels import BaseGenericLevel

class GenericLevel5(BaseGenericLevel):
    def __init__(self, screen: Surface, level_path: str, tolerance_percent: float = 2.0):
        self.tolerance_percent = tolerance_percent
        self.can_reset_pannels = True
        super().__init__(screen, level_path)
    
    def start(self):
        self.scene_manager.scene_preview = Path(self.level_path).stem
        if self.can_reset_pannels:
            self.clear_all_pannels_json()
            self.can_reset_pannels = False
        self.set_subscribes()
        self.set_resistors()
        old_paper_list = self.entity_mn.get_entities_by_class(OldPaper)
        if old_paper_list:
            self.old_paper :OldPaper= old_paper_list[0]
            self.old_paper.on_active()

    def end(self):
        self.storage_circuit.remove_all_components()
        self.storage_circuit.save_eletric_storage()
        self.clear_all_pannels_json()
        self.can_reset_pannels = True
        self.circuit_manager.clear_phase(self.level_path)

    def clear_all_pannels_json(self):
        amount_pannels = len(self.entity_mn.get_entities_by_class(ControlPannel))
        for i in range(amount_pannels):
            file_name = f'circuitos/{self.level_path}/pannel{i+1}.json'
            SerializationManager.remove_droppable_entities(file_name)

    def set_systems(self):
        self.animation_system         = AnimationSystem()
        self.area_trigger_system      = AreaTriggerSystem()
        self.freeze_system            = FreezeSystem()
        self.light_system             = LightSystem(self.screen, self.camera, debug=False, enabled=True, ambient_alpha=0)
        self.circuit_validator_system = ResistorPairValidatorSystem(level_path=self.level_path, tolerance_percent=self.tolerance_percent)

        self.systems.update([
            self.freeze_system, self.physics_system, self.animation_system,
            self.area_trigger_system, self.circuit_validator_system, self.render_system,
        ])

    def set_subscribes(self):
        self.event_manager.subscribe('set_solutions', lambda event: self.circuit_validator_system.set_solutions(event, self.entity_mn))
        self.event_manager.subscribe('solutions_done', self.set_dialogue)
        self.common_subscribes()

    def set_dialogue(self, event):
        text_list = []
        pannels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
        dialogues = self.entity_mn.get_entities_by_class(DialogueArea)
        if not dialogues:
            return
        dialogue_area: DialogueArea = dialogues[0]

        for pannel in pannels:
            solution_type = pannel.solution_type
            solution_value = pannel.solution_value
            if not solution_type or not solution_value: continue

            if solution_type == "voltage":
                parts = [f"{r_name} ≈ {SetterValues.format_eng(val, 'V')}" for r_name, val in solution_value.items()]
                text_list.append(f"Arquimedes: Para ativar o painel {pannel.pannel_id}, as tensões devem ser aproximadamente: {', '.join(parts)}")
            elif solution_type == "current":
                parts = [f"{r_name} ≈ {SetterValues.format_eng(val, 'A')}" for r_name, val in solution_value.items()]
                text_list.append(f"Arquimedes: Para ativar o painel {pannel.pannel_id}, as correntes devem ser aproximadamente: {', '.join(parts)}")

        if text_list:
            dialogue_area.add_dialogue_text(text_list)