from entities.itens.old_paper import OldPaper
from entities.itens.control_pannel import ControlPannel
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.resistor_association_validator_system import ResistorAssotiationValidatorSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.light_system import LightSystem
from pathlib import Path
from scenes.fases.generic_levels import BaseGenericLevel


class GenericLevel4(BaseGenericLevel):
    def start(self):
        self.scene_manager.scene_preview = Path(self.level_path).stem
        self.set_subscribes()
        self.set_resistors()
        old_paper_list = self.entity_mn.get_entities_by_class(OldPaper)
        if old_paper_list:
            self.old_paper :OldPaper= old_paper_list[0]
            self.old_paper.on_active()

    def set_resistors(self):
        if not self.can_set_resistors: return
        self.can_set_resistors = False
        self.storage_circuit.remove_all_components()
        self.storage_circuit.save_eletric_storage()
        self.event_manager.post({'type': 'set_solutions'})

    def end(self):
        self.storage_circuit.remove_all_components()
        self.storage_circuit.save_eletric_storage()
        self.clear_all_pannels()

    def clear_all_pannels(self):
        json_base = Path("circuitos") / self.level_path
        netlist_base = Path("ltspice") / self.level_path
        amount_pannels = len(self.entity_mn.get_entities_by_class(ControlPannel))

        for i in range(amount_pannels):
            panel_name = f"pannel{i+1}"
            edited_json = json_base / f"{panel_name}.json"
            solution_json = json_base / f"{panel_name}_solution.json"
            if solution_json.exists():
                try:
                    edited_json.write_text(solution_json.read_text(encoding="utf-8"), encoding="utf-8")
                except Exception as e:
                    pass

            edited_net = netlist_base / f"{panel_name}.net"
            solution_net = netlist_base / f"{panel_name}_solution.net"
            if solution_net.exists():
                try:
                    edited_net.write_text(solution_net.read_text(encoding="utf-8"), encoding="utf-8")
                except Exception as e:
                    pass

    def set_systems(self):
        self.animation_system         = AnimationSystem()
        self.area_trigger_system      = AreaTriggerSystem()
        self.freeze_system            = FreezeSystem()
        self.light_system             = LightSystem(self.screen, self.camera, debug=False, enabled=True, ambient_alpha=100)
        self.circuit_validator_system = ResistorAssotiationValidatorSystem(level_path=self.level_path)

        self.systems.update([
            self.freeze_system, self.physics_system, self.animation_system,
            self.area_trigger_system, self.circuit_validator_system, self.render_system,
        ])

    def set_subscribes(self):
        self.event_manager.subscribe('set_solutions', lambda event: self.circuit_validator_system.set_solutions(event, self.entity_mn))
        self.common_subscribes()