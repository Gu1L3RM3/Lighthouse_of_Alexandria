from pathlib import Path
from core.circuit_tools.SMNA import smna ,get_part_values
from core.settings import PREFIXES
import sympy
import pandas as pd
from typing import Dict, Optional, Tuple
from utils.setter_values import SetterValues

class CircuitSolver:
    
    def __init__(self, netlist_path: str):
        self.netlist_path = Path(netlist_path)

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
    def get_total_values(self) -> dict:
        if not self.is_solved:
            return None

        source_results = self.get_source_results()
        if not source_results:
            return None

        # assume uma fonte por painel (ou usa a primeira)
        _, src_info = next(iter(source_results.items()))
        V = float(src_info['voltage']['value'])
        I = float(src_info['current']['value'])
        if abs(I) < 1e-12:
            return None
        
        total_power =  abs(V*I)
        Req =  abs(V/I)


        


        return { 'voltage': {
                        'label': SetterValues.format_eng(V, 'V'),
                        'value': V
                    },
                    'current': {
                        'label': SetterValues.format_eng(I, 'A'),
                        'value': I
                    },
                    'power': {
                        'label': SetterValues.format_eng(total_power, 'W'),
                        'value': total_power
                    },
                    'resistance':{
                        'label': SetterValues.format_eng(Req,''),
                        'value': Req
                    }
                    }

    def get_equivalent_resistance(self) -> Optional[float]:
        
        if not self.is_solved:
            return None

        source_results = self.get_source_results()
        if not source_results:
            return None

        # assume uma fonte por painel (ou usa a primeira)
        _, src_info = next(iter(source_results.items()))
        V = float(src_info['voltage']['value'])
        I = float(src_info['current']['value'])

        if abs(I) < 1e-12:
            return None

        return abs(V / I)

    def get_source_results(self):
            """
            Retorna infos sobre as fontes (tensão e corrente), independente do circuito:
            - Fontes de tensão: usa corrente da MNA (I_Vx) e tensão pelos nós.
            - Fontes de corrente: usa o valor da fonte e a tensão pelos nós.

            Formato:
            {
                'V1': {
                    'type': 'voltage',
                    'voltage': {'label': '10.0 V', 'value': 10.0},
                    'current': {'label': '100 mA', 'value': 0.1},
                    'power'  : {'label': '1.0 W', 'value': 1.0}
                },
                'I1': {
                    'type': 'current',
                    'voltage': {...},
                    'current': {...},
                    'power'  : {...}
                }
            }
            """
            if not self.is_solved or self.circuit_df is None:
                return {}

            results = {}

            for _, comp in self.circuit_df.iterrows():
                element_name = comp['element']   
                first_letter = element_name[0].lower()

                if first_letter not in ('v', 'i'):
                    continue

                p_node = int(comp['p node'])
                n_node = int(comp['n node'])
                value  = comp['value'] 

                v_p = 0.0 if p_node == 0 else float(self.solution.get(sympy.Symbol(f'v{p_node}'), 0.0))
                v_n = 0.0 if n_node == 0 else float(self.solution.get(sympy.Symbol(f'v{n_node}'), 0.0))

         
                voltage_across = -v_p + v_n

                if first_letter == 'v':
                    I_symbol = sympy.Symbol(f'I_{element_name}')
                    current = float(self.solution.get(I_symbol, 0.0))

                    src_type = 'voltage'

                else:
                    current = float(value)
                    src_type = 'current'

                power = voltage_across * current  

                results[element_name] = {
                    'type': src_type,
                    'voltage': {
                        'label': SetterValues.format_eng(voltage_across, 'V'),
                        'value': voltage_across
                    },
                    'current': {
                        'label': SetterValues.format_eng(current, 'A'),
                        'value': current
                    },
                    'power': {
                        'label': SetterValues.format_eng(power, 'W'),
                        'value': power
                    }
                }

            return results


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