import SMNA
import sympy
import pandas as pd
from typing import Dict


def get_circuit(path: str) -> str:
    """Le, limpa e retorna o conteudo da netlist como uma string."""
    circuit = ""
    with open(path, "r", encoding="utf-8") as file:
        except_texts = (".", "*")
        for line in file.readlines():
            if line.startswith(except_texts):
                continue
            clear_line = line.strip()
            if not clear_line:
                continue
            clear_line = clear_line.lower().replace("k", "e3").replace("meg", "e6")
            clear_line = clear_line.replace("m", "e-3").replace("u", "e-6").replace("n", "e-9")
            circuit += f"{clear_line}\n"
    return circuit


def analyze_resistors(
    mna_solution: Dict[sympy.Symbol, float],
    circuit_df: pd.DataFrame,
) -> Dict[str, Dict[str, float]]:
    """
    Calcula tensao e corrente para cada resistor no circuito.
    """
    resistor_results = {}

    for _, component in circuit_df.iterrows():
        element_name = component["element"]
        if not element_name.lower().startswith("r"):
            continue

        p_node = int(component["p node"])
        n_node = int(component["n node"])
        resistance = component["value"]

        voltage_p = 0 if p_node == 0 else mna_solution.get(sympy.Symbol(f"v{p_node}"), 0)
        voltage_n = 0 if n_node == 0 else mna_solution.get(sympy.Symbol(f"v{n_node}"), 0)

        voltage_across = voltage_p - voltage_n
        current_through = voltage_across / resistance if resistance != 0 else 0

        resistor_results[element_name] = {
            "voltage": voltage_across,
            "current": current_through,
        }

    return resistor_results


def main():
    netlist_path = "circuito.net"
    circuito = get_circuit(netlist_path)
    _, df, _, A, X, Z = SMNA.smna(circuito)

    try:
        solucao_simbolica = sympy.solve(A * sympy.Matrix(X) - sympy.Matrix(Z), X)
        if not solucao_simbolica:
            raise Exception("O sistema nao tem uma solucao unica.")

        valores_componentes = SMNA.get_part_values(df)
        solucao_numerica = {
            var: formula.subs(valores_componentes).evalf()
            for var, formula in solucao_simbolica.items()
        }

        _ = analyze_resistors(solucao_numerica, df)
    except Exception:
        pass


if __name__ == "__main__":
    main()
