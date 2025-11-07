from core.circuit_tools.SMNA import smna ,get_part_values
import sympy
import pandas as pd
from typing import Dict, Optional, Tuple

class CircuitSolver:
    
    def __init__(self, netlist_path: str):
        # ... (O construtor e outras funções permanecem os mesmos) ...
        self.netlist_path = netlist_path
        self.report: Optional[str] = None
        self.circuit_df: Optional[pd.DataFrame] = None
        self.solution: Dict[sympy.Symbol, float] = {}
        self.is_solved = False

        self._solve_circuit()

    @staticmethod
    def format_eng(value: float, unit: str) -> str:
        """
        Formata um número float em uma string com notação de engenharia.

        Args:
            value: O número a ser formatado.
            unit: A unidade base (ex: 'V', 'A', 'Hz').

        Returns:
            Uma string formatada (ex: "1.23 kV", "500.00 µA").
        """
        if value == 0:
            return f"0.00{unit}"

        prefixes = [
            (1e12, 'T'), (1e9, 'G'), (1e6, 'M'), (1e3, 'k'),
            (1, ''),
            (1e-3, 'm'), (1e-6, 'µ'), (1e-9, 'n'), (1e-12, 'p')
        ]

        for multiplier, prefix in prefixes:
            if abs(value) >= multiplier:
                scaled_value = value / multiplier
                return f"{scaled_value:.2f}{prefix}{unit}"
        
        return f"{value:.2e}{unit}"

    def _load_and_clean_netlist(self) -> str:
        circuit_str = ''
        try:
            with open(self.netlist_path, "r", encoding="utf-8") as file:
                for line in file.readlines():
                    if line.startswith(('.', '*')):
                        continue
                    clear_line = line.strip()
                    if not clear_line:
                        continue
                    clear_line=clear_line.replace("N00","")
                    clear_line = clear_line.lower().replace('k', 'e3').replace('meg', 'e6')
                    clear_line = clear_line.replace('m', 'e-3').replace('u', 'e-6').replace('n', 'e-9')
                    circuit_str += f"{clear_line}\n"
            return circuit_str
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de netlist não encontrado em: {self.netlist_path}")

    def _solve_circuit(self):
        try:
            netlist_content = self._load_and_clean_netlist()
            
            self.report, self.circuit_df, _, A, X, Z = smna(netlist_content)
            
            symbolic_solution = sympy.solve(A * sympy.Matrix(X) - sympy.Matrix(Z), X)
            if not symbolic_solution:
                raise RuntimeError("O sistema não tem uma solução única (pode ser indeterminado).")

            component_values = get_part_values(self.circuit_df)
            self.solution = {
                var: formula.subs(component_values).evalf()
                for var, formula in symbolic_solution.items()
            }
            self.is_solved = True
            
        except Exception as e:
            print(f"ERRO: Falha ao analisar ou resolver o circuito '{self.netlist_path}'.")
            print(f"Detalhe: {e}")
            self.is_solved = False

    def get_node_voltages(self) -> Dict[str, float]:
        if not self.is_solved:
            return {}
        
        return {
            str(var): float(val)
            for var, val in self.solution.items()
            if str(var).startswith('v')
        }

    def get_resistor_results(self) -> Dict[str, Dict[str, str]]:
        """
        
        Returns:
            Um dicionário no formato: 
            {'R0': {'voltage': '10.00 V', 'current': '100.00 µA'}}
        """
        if not self.is_solved or self.circuit_df is None:
            return {}
            
        resistor_results = {}
        for _, component in self.circuit_df.iterrows():
            element_name = component['element']
            if element_name.lower().startswith('r'):
                p_node = int(component['p node'])
                n_node = int(component['n node'])
                resistance = component['value']

                voltage_p = 0 if p_node == 0 else self.solution.get(sympy.Symbol(f'v{p_node}'), 0)
                voltage_n = 0 if n_node == 0 else self.solution.get(sympy.Symbol(f'v{n_node}'), 0)
                
                voltage_across =  voltage_p +  voltage_n
                current_through = -voltage_across / resistance if resistance != 0 else 0

                resistor_results[element_name] = {
                    'voltage': self.format_eng(float(voltage_across), 'V'),
                    'current': self.format_eng(float(current_through), 'A')
                }
        return resistor_results