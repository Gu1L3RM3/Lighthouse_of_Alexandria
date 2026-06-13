from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.circuit_tools.serialization_manager import SerializationManager
from core.circuit_tools.solve_circuit import CircuitSolver


def _clamp(value: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(max_v, value))


@dataclass
class BombParams:
    voltage_r1: float
    current_r1: float
    explosion_delay: float
    explosion_radius: float
    damage: float
    used_fallback: bool = False


class BombManager:
    """
    Converte parametros de R1 (V e I) em comportamento da bomba.
    Se o circuito estiver invalido, usa configuracao padrao segura.
    """

    def __init__(self, bombs_per_level: int = 4, default_netlist_path: str | Path | None = None):
        self.max_bombs = max(0, int(bombs_per_level))
        self.remaining_bombs = self.max_bombs
        self._default_netlist_path = default_netlist_path

        self.set_balance_profile("standard")

        self.default_params = self._build_default_params(self._default_netlist_path)
        self.current_params = self.default_params

    def set_balance_profile(self, profile: str):
        _ = profile
        # Mantemos a API por compatibilidade, mas usamos um unico perfil fixo.
        values = {
            "delay_min": 1.20,
            "delay_max": 2.40,
            "radius_min": 42.0,
            "radius_max": 140.0,
            "damage_min": 12.0,
            "damage_max": 180.0,
            "k_delay": 0.06,
            "k_radius": 1800.0,
            "k_damage": 850.0,
        }

        self._delay_min = float(values["delay_min"])
        self._delay_max = float(values["delay_max"])
        self._radius_min = float(values["radius_min"])
        self._radius_max = float(values["radius_max"])
        self._damage_min = float(values["damage_min"])
        self._damage_max = float(values["damage_max"])
        self._k_delay = float(values["k_delay"])
        self._k_radius = float(values["k_radius"])
        self._k_damage = float(values["k_damage"])

        if hasattr(self, "default_params"):
            self.default_params = self._build_default_params(self._default_netlist_path)
            if getattr(self.current_params, "used_fallback", False):
                self.current_params = self.default_params

    def _build_default_params(self, default_netlist_path: str | Path | None) -> BombParams:
        # Fallback final caso o netlist padrao nao seja carregado.
        hardcoded = BombParams(
            voltage_r1=4.0,
            current_r1=0.02,
            explosion_delay=1.5,
            explosion_radius=56.0,
            damage=40.0,
            used_fallback=True,
        )
        if default_netlist_path is None:
            return hardcoded

        try:
            netlist_text = SerializationManager.load_netlist_text(default_netlist_path)
            solver = (
                CircuitSolver.from_netlist_content(netlist_text)
                if netlist_text is not None
                else CircuitSolver(str(default_netlist_path))
            )
            if not solver.is_solved:
                return hardcoded
            resistor_results = solver.get_resistor_results()
            target = resistor_results.get("R1")
            if not target:
                return hardcoded
            v_raw = float(target["voltage"]["value"])
            i_raw = float(target["current"]["value"])
            v = abs(v_raw)
            i = abs(i_raw)
            return BombParams(
                voltage_r1=v_raw,
                current_r1=i_raw,
                explosion_delay=_clamp(self._delay_max - (v * self._k_delay), self._delay_min, self._delay_max),
                explosion_radius=_clamp(i * self._k_radius, self._radius_min, self._radius_max),
                damage=_clamp((v * i) * self._k_damage, self._damage_min, self._damage_max),
                used_fallback=False,
            )
        except Exception:
            return hardcoded

    def reset_bombs(self, bombs_per_level: int | None = None):
        if bombs_per_level is not None:
            self.max_bombs = max(0, int(bombs_per_level))
        self.remaining_bombs = self.max_bombs

    def can_use_bomb(self) -> bool:
        return self.remaining_bombs > 0

    def consume_bomb(self) -> bool:
        if not self.can_use_bomb():
            return False
        self.remaining_bombs -= 1
        return True

    def update_from_resistor_results(self, resistor_results: dict | None, target_resistor: str = "R1"):
        if not resistor_results:
            self.current_params = self.default_params
            return

        target = resistor_results.get(target_resistor)
        if not target:
            self.current_params = self.default_params
            return

        try:
            v_raw = float(target["voltage"]["value"])
            i_raw = float(target["current"]["value"])
            v = abs(v_raw)
            i = abs(i_raw)

            explosion_delay = _clamp(
                self._delay_max - (v * self._k_delay),
                self._delay_min,
                self._delay_max,
            )
            explosion_radius = _clamp(
                i * self._k_radius,
                self._radius_min,
                self._radius_max,
            )
            damage = _clamp(
                (v * i) * self._k_damage,
                self._damage_min,
                self._damage_max,
            )
            self.current_params = BombParams(
                voltage_r1=v_raw,
                current_r1=i_raw,
                explosion_delay=explosion_delay,
                explosion_radius=explosion_radius,
                damage=damage,
                used_fallback=False,
            )
        except Exception:
            self.current_params = self.default_params
