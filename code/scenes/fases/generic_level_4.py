from entities.itens.old_paper import OldPaper
from entities.itens.control_pannel import ControlPannel
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.resistor_association_validator_system import ResistorAssotiationValidatorSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.phantom_ai_system import PhantomAISystem
from core.systems.enemy_touch_game_over_system import EnemyTouchGameOverSystem
from core.systems.spider_web_system import SpiderWebSystem
from core.ui.widgets.stealth_timer_bar_widget import StealthTimerBarWidget
from core.components.animation_sprite import AnimateSprite
from core.components.freeze import Freeze
from core.settings import path_in_circuitos, path_in_ltspice
from pathlib import Path
from scenes.fases.generic_levels import BaseGenericLevel


class GenericLevel4(BaseGenericLevel):
    def start(self):
        self.scene_manager.scene_preview = Path(self.level_path).stem
        self.player_dead_by_enemy = False
        self.phantom_ai_system.set_touch_triggered(False)
        self.enemy_touch_game_over_system.triggered = False
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
        if self._should_skip_progress_reset_on_end():
            return
        self.storage_circuit.remove_all_components()
        self.storage_circuit.save_eletric_storage()
        self.clear_all_pannels()

    def clear_all_pannels(self):
        json_base = path_in_circuitos(self.level_path)
        netlist_base = path_in_ltspice(self.level_path)
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
        self.phantom_ai_system        = PhantomAISystem(self.tile_map)
        self.spider_web_system        = SpiderWebSystem()
        self.enemy_touch_game_over_system = EnemyTouchGameOverSystem()
        self.stealth_timer_widget = StealthTimerBarWidget(self.screen.get_size(), self.phantom_ai_system)
        self.ui_manager.add(self.stealth_timer_widget)
        self.circuit_validator_system = ResistorAssotiationValidatorSystem(level_path=self.level_path)

        self.systems.update([
            self.freeze_system,
            self.phantom_ai_system,
            self.path_following_system,
            self.spider_web_system,
            self.enemy_touch_game_over_system,
            self.physics_system,
            self.animation_system,
            self.area_trigger_system, self.circuit_validator_system, self.render_system,
        ])

    def set_subscribes(self):
        self.event_manager.subscribe('set_solutions', lambda event: self.circuit_validator_system.set_solutions(event, self.entity_mn))
        self.event_manager.subscribe("player_invisible_to_enemies_started", self.phantom_ai_system.on_crystal_collected)
        self.event_manager.subscribe("cancel_reaggro_after_invisibility", self.phantom_ai_system.on_flask_collected)
        self.event_manager.subscribe('player_touched_enemy', self.on_player_touched_enemy)
        self.common_subscribes()

    def on_player_touched_enemy(self, event):
        _ = event
        if self.player_dead_by_enemy:
            return
        self.player_dead_by_enemy = True
        self.phantom_ai_system.set_touch_triggered(True)
        player = self.entity_mn.get_player()
        if not player:
            self.death_flow_manager.handle_player_death()
            return

        if player.has(Freeze):
            player.get(Freeze).active = True

        if player.has(AnimateSprite):
            anim: AnimateSprite = player.get(AnimateSprite)
            dir_name = "front"
            if hasattr(player, "_get_dir_name") and hasattr(player, "old_direction"):
                dir_name = player._get_dir_name(player.old_direction)
            anim.play(
                f"death_{dir_name}",
                reset=True,
                loop=False,
                on_finish=lambda: self.death_flow_manager.handle_player_death(),
            )
            return

        self.death_flow_manager.handle_player_death()
