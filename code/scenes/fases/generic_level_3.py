from core.settings import *
from entities.dialogue_area import DialogueArea
from entities.itens.old_paper import OldPaper
from entities.itens.control_pannel import ControlPannel
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.circuit_validator_system import CircuitValidatorSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.light_system import LightSystem
from core.circuit_tools.serialization_manager import SerializationManager
from utils.setter_values import SetterValues
from pathlib import Path
from scenes.fases.generic_levels import BaseGenericLevel


class GenericLevel3(BaseGenericLevel):
    def start(self):
        self.scene_manager.scene_preview = Path(self.level_path).stem
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
        self.circuit_validator_system = CircuitValidatorSystem(level_path=self.level_path)
        self.systems.update([
            self.freeze_system, self.physics_system, self.animation_system,
            self.area_trigger_system, self.circuit_validator_system, self.render_system
        ])

    def set_subscribes(self):
        self.event_manager.subscribe('set_solutions',lambda event :self.circuit_validator_system.set_solutions(event,self.entity_mn))
        self.event_manager.subscribe('solutions_done',self.set_dialogue)
        self.common_subscribes()

    def set_dialogue(self,event):
        text_list = []
        pannels :list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
        dialogues = self.entity_mn.get_entities_by_class(DialogueArea)
        if not dialogues:
            return
        dialogue_area :DialogueArea = dialogues[0]
        
        for pannel in pannels:
            st = pannel.solution_type
            if st == "voltage":
                text_list.append(f"Arquimedes: Para ativar o painel {pannel.pannel_id} o resistor {pannel.target_component} deve ter tensão próxima de {SetterValues.format_eng(pannel.solution_value,'V')}")
            elif st == "power":
                text_list.append(f"Arquimedes: Para ativar o painel {pannel.pannel_id} o resistor {pannel.target_component} deve ter potência próxima de {SetterValues.format_eng(pannel.solution_value,'W')}")
            elif st == "current":
                text_list.append(f"Arquimedes: Para ativar o painel {pannel.pannel_id} o resistor {pannel.target_component} deve ter corrente próxima de {SetterValues.format_eng(pannel.solution_value,'A')}")
        dialogue_area.add_dialogue_text(text_list)