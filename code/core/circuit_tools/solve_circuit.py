from core.circuit_tools.SMNA import smna ,get_part_values
from core.settings import PREFIXES
import sympy
import pandas as pd
from typing import Dict, Optional, Tuple
from utils.setter_values import SetterValues

class CircuitSolver:
    
    def __init__(self, netlist_path: str):
        self.netlist_path = netlist_path
        self.report: Optional[str] = None
        self.circuit_df: Optional[pd.DataFrame] = None
        self.solution: Dict[sympy.Symbol, float] = {}
        self.is_solved = False

        self._solve_circuit()

    

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
            {'R0': {'voltage': '10.00 V', 'current': '100.00 µA','power': '1.0 mW'}}
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
                voltage_across =  -voltage_p  + voltage_n
                current_through = voltage_across / resistance if resistance != 0 else 0
                power =  voltage_across*current_through
                resistor_results[element_name] = {
                    'voltage': {'label':SetterValues.format_eng(float(voltage_across), 'V'),'value':voltage_across},
                    'current': {'label':SetterValues.format_eng(float(current_through), 'A'),'value':current_through},
                    'power'  : {'label':SetterValues.format_eng(float(power),'W'),'value':power}
                }
        return resistor_results