import SMNA 
import sympy
import pandas as pd
from typing import Dict
def get_circuit(path:str)->str:
    """Lê, limpa e retorna o conteúdo da netlist como uma string."""
    circuit = ''
    with open(path,"r",encoding="utf-8") as file:
        except_texts = ('.','*')
        for line in file.readlines():
            if line.startswith(except_texts):
                continue
            clear_line = line.strip()
            if not clear_line:
                continue
            # Converte '100k' para '100e3' para ser compatível com float()
            clear_line = clear_line.lower().replace('k','e3').replace('meg','e6')
            clear_line = clear_line.replace('m','e-3').replace('u','e-6').replace('n','e-9')
            circuit +=f"{clear_line}\n"
    return circuit


def analyze_resistors(
    mna_solution: Dict[sympy.Symbol, float], 
    circuit_df: pd.DataFrame
) -> Dict[str, Dict[str, float]]:
    """
    Calcula a tensão e a corrente para cada resistor no circuito.

    Args:
        mna_solution: Um dicionário com as tensões nodais e correntes de fontes 
                      resolvidas pela análise MNA. Ex: {v1: 20.0, v2: 10.0, ...}
        circuit_df: O DataFrame do pandas contendo a descrição do circuito,
                    gerado pela função smna.

    Returns:
        Um dicionário onde cada chave é o nome de um resistor (ex: 'R0') e
        o valor é outro dicionário com as chaves 'voltage' e 'current'.
        Ex: {'R0': {'voltage': 10.0, 'current': 0.0001}}
    """
    resistor_results = {}

    # Itera sobre cada componente no DataFrame do circuito
    for _, component in circuit_df.iterrows():
        element_name = component['element']

        # Processa apenas se o componente for um resistor
        if element_name.lower().startswith('r'):
            p_node = int(component['p node'])
            n_node = int(component['n node'])
            resistance = component['value']

            # Obtém a tensão em cada nó. A tensão no nó 0 (terra) é sempre 0.
            voltage_p = 0 if p_node == 0 else mna_solution.get(sympy.Symbol(f'v{p_node}'), 0)
            voltage_n = 0 if n_node == 0 else mna_solution.get(sympy.Symbol(f'v{n_node}'), 0)
            
            # Aplica a Lei de Ohm
            voltage_across = voltage_p - voltage_n
            current_through = voltage_across / resistance if resistance != 0 else 0

            # Adiciona o resultado ao dicionário
            resistor_results[element_name] = {
                'voltage': voltage_across,
                'current': current_through
            }
            
    return resistor_results
netlist_path = "circuito.net"
circuito = get_circuit(netlist_path)
report, df, df2, A, X, Z = SMNA.smna(circuito)

print("--- Relatório da Netlist ---")
print(report)

try:
    # --- PASSO 2: Resolver o Sistema e Obter Solução Numérica ---
    solucao_simbolica = sympy.solve(A * sympy.Matrix(X) - sympy.Matrix(Z), X)
    if not solucao_simbolica:
        raise Exception("O sistema não tem uma solução única.")

    valores_componentes = SMNA.get_part_values(df)
    
    solucao_numerica = {
        var: formula.subs(valores_componentes).evalf()
        for var, formula in solucao_simbolica.items()
    }
    
    print("\n--- Solução MNA (Tensões nos Nós) ---")
    for var, val in solucao_numerica.items():
        if str(var).startswith('v'):
            print(f"{var} = {val:.4f} V")

    # --- PASSO 3: Usar a nova função para obter os resultados dos resistores ---
    resultados_resistores = analyze_resistors(solucao_numerica, df)

    print(resultados_resistores)

    # # --- PASSO 4: Exibir os resultados de forma organizada ---
    # print("\n--- Resultados nos Resistores ---")
    # for resistor, valores in resultados_resistores.items():
    #     tensao = valores['voltage']
    #     corrente = valores['current']
        
    #     print(f"Resistor: {resistor}")
    #     print(f"  - Tensão: {tensao:.4f} V")
    #     # Exibindo corrente em miliamperes (mA) para melhor leitura
    #     print(f"  - Corrente: {corrente * 1000:.4f} mA")

except Exception as e:
    print(f"\nERRO: Não foi possível resolver o circuito.")
    print(f"Detalhe: {e}")