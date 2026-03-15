from pathlib import Path
from core.circuit_tools.SMNA import smna, get_part_values
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
                    clear_line = clear_line.replace("N00", "")
                    clear_line = clear_line.lower().replace('k', 'e3').replace('meg', 'e6')
                    clear_line = clear_line.replace('m', 'e-3').replace('u', 'e-6').replace('n', 'e-9')
                    circuit_str += f"{clear_line}\n"
            return circuit_str
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de netlist não encontrado em: {self.netlist_path}")

    def _solve_netlist_string(
        self,
        netlist_content: str
    ) -> Tuple[str, pd.DataFrame, Dict[sympy.Symbol, float]]:
        """
        Resolve qualquer netlist em string e retorna:
        report, dataframe do circuito e solução numérica.
        """
        report, circuit_df, _, A, X, Z = smna(netlist_content)

        symbolic_solution = sympy.solve(A * sympy.Matrix(X) - sympy.Matrix(Z), X)
        if not symbolic_solution:
            raise RuntimeError("O sistema não tem uma solução única (pode ser indeterminado).")

        component_values = get_part_values(circuit_df)
        numeric_solution = {
            var: formula.subs(component_values).evalf()
            for var, formula in symbolic_solution.items()
        }

        return report, circuit_df, numeric_solution

    def _solve_circuit(self):
        try:
            netlist_content = self._load_and_clean_netlist()
            self.report, self.circuit_df, self.solution = self._solve_netlist_string(netlist_content)
            self.is_solved = True
        except Exception:
            self.is_solved = False

    def _get_component_row(self, component_name: str) -> Optional[pd.Series]:
        if self.circuit_df is None:
            return None

        rows = self.circuit_df[
            self.circuit_df['element'].astype(str).str.lower() == component_name.lower()
        ]
        if rows.empty:
            return None
        return rows.iloc[0]

    def _get_component_nodes(self, component_name: str) -> Optional[Tuple[int, int]]:
        row = self._get_component_row(component_name)
        if row is None:
            return None
        return int(row['p node']), int(row['n node'])

    def _remove_component_from_netlist(self, netlist_content: str, component_name: str) -> str:
        """
        Remove do netlist a linha cujo primeiro token seja o nome do componente.
        Ex.: remove 'R1 ...'
        """
        new_lines = []

        for line in netlist_content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            tokens = stripped.split()
            if not tokens:
                continue

            if tokens[0].lower() == component_name.lower():
                continue

            new_lines.append(stripped)

        return "\n".join(new_lines) + ("\n" if new_lines else "")

    def _deactivate_independent_sources(self, netlist_content: str) -> str:
        """
        Desativa somente fontes independentes:
        - Vx -> 0 V (curto)
        - Ix -> removida (0 A = circuito aberto)
        """
        new_lines = []

        for line in netlist_content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            tokens = stripped.split()
            if not tokens:
                continue

            element_name = tokens[0].lower()

            if element_name.startswith('v'):
                # Fonte de tensão independente -> 0 V
                if len(tokens) >= 4:
                    new_lines.append(f"{tokens[0]} {tokens[1]} {tokens[2]} 0")
                else:
                    new_lines.append(stripped)

            elif element_name.startswith('i'):
                # Fonte de corrente independente -> circuito aberto
                continue

            else:
                new_lines.append(stripped)

        return "\n".join(new_lines) + ("\n" if new_lines else "")

    def _get_node_voltage_from_solution(
        self,
        solution: Dict[sympy.Symbol, float],
        node: int
    ) -> float:
        if node == 0:
            return 0.0
        return float(solution.get(sympy.Symbol(f'v{node}'), 0.0))

    def _get_voltage_between_nodes(
        self,
        solution: Dict[sympy.Symbol, float],
        p_node: int,
        n_node: int
    ) -> float:
        """
        Mantém a mesma convenção já usada no restante da classe:
        V = -Vp + Vn
        """
        v_p = self._get_node_voltage_from_solution(solution, p_node)
        v_n = self._get_node_voltage_from_solution(solution, n_node)
        return -v_p + v_n

    def _find_test_source_current(
        self,
        solved_df: pd.DataFrame,
        solved_solution: Dict[sympy.Symbol, float],
        test_source_name: str
    ) -> float:
        """
        Encontra a corrente associada à fonte de teste.
        Como o SMNA capitaliza o nome, procuramos no df resolvido o nome real.
        """
        rows = solved_df[
            solved_df['element'].astype(str).str.lower() == test_source_name.lower()
        ]
        if rows.empty:
            raise RuntimeError(f"Fonte de teste '{test_source_name}' não encontrada no circuito resolvido.")

        real_name = str(rows.iloc[0]['element'])
        i_symbol = sympy.Symbol(f'I_{real_name}')

        if i_symbol not in solved_solution:
            raise RuntimeError(f"Corrente da fonte de teste '{real_name}' não encontrada na solução.")

        return float(solved_solution[i_symbol])

    def get_total_values(self) -> dict:
        if not self.is_solved:
            return None

        source_results = self.get_source_results()
        if not source_results:
            return None

        _, src_info = next(iter(source_results.items()))
        V = float(src_info['voltage']['value'])
        I = float(src_info['current']['value'])
        if abs(I) < 1e-12:
            return None
        
        total_power = abs(V * I)
        Req = abs(V / I)

        return {
            'voltage': {
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
            'resistance': {
                'label': SetterValues.format_eng(Req, ''),
                'value': Req
            }
        }

    def get_equivalent_resistance(self) -> Optional[float]:
        if not self.is_solved:
            return None

        source_results = self.get_source_results()
        if not source_results:
            return None

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
            value = comp['value']

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
            {'R0': {'voltage': '10.00 V', 'current': '100.00 µA', 'power': '1.0 mW'}}
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
                voltage_across = -voltage_p + voltage_n
                current_through = voltage_across / resistance if resistance != 0 else 0
                power = voltage_across * current_through

                resistor_results[element_name] = {
                    'voltage': {
                        'label': SetterValues.format_eng(float(voltage_across), 'V'),
                        'value': voltage_across
                    },
                    'current': {
                        'label': SetterValues.format_eng(float(current_through), 'A'),
                        'value': current_through
                    },
                    'power': {
                        'label': SetterValues.format_eng(float(power), 'W'),
                        'value': power
                    }
                }
        return resistor_results

    def get_thevenin(self, component_name: str) -> Optional[dict]:
        """
        Calcula o equivalente de Thévenin visto pelos terminais do componente informado.
        Ex.: get_thevenin("R1")

        Passos:
        1) encontra os terminais do componente
        2) remove o componente
        3) calcula Vth = tensão em circuito aberto
        4) desativa fontes independentes
        5) insere fonte de teste de 1V
        6) calcula Rth = 1 / Iteste
        """
        if not self.is_solved or self.circuit_df is None:
            return None

        component_nodes = self._get_component_nodes(component_name)
        if component_nodes is None:
            return None

        p_node, n_node = component_nodes

        try:
            original_netlist = self._load_and_clean_netlist()

            # Remove a carga
            netlist_without_component = self._remove_component_from_netlist(
                original_netlist,
                component_name
            )

            # 1) Vth -> tensão em circuito aberto
            _, open_df, open_solution = self._solve_netlist_string(netlist_without_component)
            vth = self._get_voltage_between_nodes(open_solution, p_node, n_node)

            # 2) Rth -> fonte de teste com fontes independentes desligadas
            passive_netlist = self._deactivate_independent_sources(netlist_without_component)

            test_source_name = "VTEST_TH"
            test_netlist = passive_netlist + f"{test_source_name} {p_node} {n_node} 1\n"

            _, test_df, test_solution = self._solve_netlist_string(test_netlist)

            i_test = self._find_test_source_current(test_df, test_solution, test_source_name)

            if abs(i_test) < 1e-12:
                return None

            rth = abs(1.0 / i_test)

            return {
                'component': component_name,
                'terminals': {
                    'p_node': p_node,
                    'n_node': n_node
                },
                'voltage': {
                    'label': SetterValues.format_eng(float(vth), 'V'),
                    'value': float(vth)
                },
                'resistance': {
                    'label': SetterValues.format_eng(float(rth), ''),
                    'value': float(rth)
                }
            }

        except Exception:
            return None

    def get_norton(self, component_name: str) -> Optional[dict]:
        """
        Calcula o equivalente de Norton visto pelos terminais do componente informado.
        Ex.: get_norton("R1")

        Usa:
        - In = Vth / Rth
        - Rn = Rth
        """
        thevenin = self.get_thevenin(component_name)
        if thevenin is None:
            return None

        vth = float(thevenin['voltage']['value'])
        rth = float(thevenin['resistance']['value'])

        if abs(rth) < 1e-12:
            return None

        inorton = vth / rth
        rnorton = rth

        return {
            'component': component_name,
            'terminals': thevenin['terminals'],
            'current': {
                'label': SetterValues.format_eng(float(inorton), 'A'),
                'value': float(inorton)
            },
            'resistance': {
                'label': SetterValues.format_eng(float(rnorton), ''),
                'value': float(rnorton)
            }
        }