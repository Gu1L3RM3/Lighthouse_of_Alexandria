import json
from collections import deque
from pathlib import Path

# Constante para o tamanho da célula da grade, inferido do JSON
CELL_SIZE = 64

class LtSpiceGenerate:
    """
    Gera uma netlist SPICE a partir de um arquivo de descrição de circuito em JSON.
    Esta classe é autônoma e processa diretamente a estrutura de dados do JSON.
    """
    def __init__(self, json_filepath: str):
        """
        Inicializa o gerador lendo um arquivo JSON do disco.
        :param json_filepath: O caminho para o arquivo circuit.json.
        """
        # --- CORREÇÃO APLICADA AQUI ---
        # 1. Abre o arquivo localizado no caminho fornecido.
        # 2. Lê todo o conteúdo do arquivo como uma única string.
        # 3. Usa json.loads() para analisar essa string de conteúdo.
        try:
            json_content_string = Path(json_filepath).read_text(encoding="utf-8")
            self.circuit_data = json.loads(json_content_string)
        except FileNotFoundError:
            print(f"ERRO: O arquivo de circuito '{json_filepath}' não foi encontrado.")
            self.circuit_data = [] # Inicializa com dados vazios para evitar mais erros
        except json.JSONDecodeError as e:
            print(f"ERRO: O arquivo '{json_filepath}' não contém um JSON válido. {e}")
            self.circuit_data = []

    def _get_terminals(self, entity: dict) -> dict[str, tuple[int, int]]:
        """
        Calcula as coordenadas exatas dos terminais para uma única entidade do JSON.
        """
        comp_map = {c['type']: c for c in entity['components']}
        pos = comp_map.get('Position')
        conn = comp_map.get('Connectable')
        spr = comp_map.get('Sprite')
        
        if not all((pos, conn, spr)):
            return {}

        x, y = pos['x'], pos['y']
        angle = spr['angle']
        entity_type = entity['entity_type']
        
        center_x, center_y = x + CELL_SIZE / 2, y + CELL_SIZE / 2

        if entity_type in ['Node', 'Wire', 'Ground']:
            terminals = {}
            if 'up' in conn['connections'] or 'top' in conn['connections']:
                terminals['top'] = (center_x, y)
            if 'down' in conn['connections'] or 'bottom' in conn['connections']:
                terminals['bottom'] = (center_x, y + CELL_SIZE)
            if 'left' in conn['connections']:
                terminals['left'] = (x, center_y)
            if 'right' in conn['connections']:
                terminals['right'] = (x + CELL_SIZE, center_y)
            return terminals

        elif entity_type in ['Resistor', 'VoutageSource', 'CurrentSource']:
            terminals = {}
            if angle in [0, 180]: # Horizontal
                terminals['left'] = (x, center_y)
                terminals['right'] = (x + 2 * CELL_SIZE, center_y)
            elif angle in [90, 270]: # Vertical
                terminals['top'] = (center_x, y)
                terminals['bottom'] = (center_x, y + 2 * CELL_SIZE)
            
            if entity_type == 'Resistor': return {'a': terminals.get('left') or terminals.get('top'), 'b': terminals.get('right') or terminals.get('bottom')}
            if entity_type == 'VoutageSource': return {'neg': terminals.get('top') or terminals.get('left'), 'pos': terminals.get('bottom') or terminals.get('right')}
            if entity_type == 'CurrentSource': return {'a': terminals.get('top') or terminals.get('left'), 'b': terminals.get('bottom') or terminals.get('right')}
        
        return {}

    def generate_netlist(self) -> list[str]:
        """
        Executa a lógica principal de descoberta de nós e geração da netlist.
        """
        if not self.circuit_data: # Se o carregamento do JSON falhou, retorna uma lista vazia
            return []
            
        coord_map = {}
        all_terminals = []
        
        for i, entity in enumerate(self.circuit_data):
            entity['id'] = i
            for term_name, pos in self._get_terminals(entity).items():
                terminal_id = (entity['id'], term_name)
                all_terminals.append(terminal_id)
                if pos not in coord_map: coord_map[pos] = []
                coord_map[pos].append(terminal_id)
        
        terminal_to_node = {}
        visited_terminals = set()
        node_counter = 1
        
        for entity_id, start_term_name in all_terminals:
            if (entity_id, start_term_name) in visited_terminals:
                continue
            
            q = deque([(entity_id, start_term_name)])
            current_node_terminals = set()
            is_ground_node = False
            
            while q:
                curr_id, curr_term_name = q.popleft()
                if (curr_id, curr_term_name) in visited_terminals: continue
                
                visited_terminals.add((curr_id, curr_term_name))
                current_node_terminals.add((curr_id, curr_term_name))
                
                curr_entity = self.circuit_data[curr_id]
                if curr_entity['entity_type'] == 'Ground':
                    is_ground_node = True
                
                term_pos = self._get_terminals(curr_entity).get(curr_term_name)
                if term_pos in coord_map:
                    for neighbor_id, neighbor_term_name in coord_map[term_pos]:
                        if (neighbor_id, neighbor_term_name) not in visited_terminals:
                            q.append((neighbor_id, neighbor_term_name))
                
                if curr_entity['entity_type'] in ['Wire', 'Node']:
                    for other_term_name in self._get_terminals(curr_entity):
                        if (curr_id, other_term_name) not in visited_terminals:
                            q.append((curr_id, other_term_name))

            node_name = "0" if is_ground_node else f"N{node_counter:03d}"
            for t_id, t_name in current_node_terminals:
                terminal_to_node[(t_id, t_name)] = node_name
            
            if not is_ground_node: node_counter += 1

        netlist_lines = []
        netlist_components = [e for e in self.circuit_data if e['entity_type'] in ['Resistor', 'VoutageSource', 'CurrentSource']]
        
        for comp in netlist_components:
            label_comp = next((c for c in comp['components'] if c['type'] == 'LabelComponent'), None)
            if not label_comp: continue

            name = label_comp['name']
            value = label_comp['value']
            
            terminals = self._get_terminals(comp)
            node_names = [
                terminal_to_node.get((comp['id'], term_name))
                for term_name, _ in sorted(terminals.items())
            ]
            
            if len(node_names) == 2:
                netlist_lines.append(f"{name} {node_names[0]} {node_names[1]} {value}")
                
        return netlist_lines
        
    def save_netlist(self, out_file="circuito.net"):
        """Salva a netlist gerada em um arquivo."""
        netlist = self.generate_netlist()
        header = ["* Netlist gerada automaticamente a partir do circuit.json", ".tran 1", ""]
        content = "\n".join(header + netlist + ["", ".end"])
        Path(out_file).write_text(content, encoding="utf-8")
        print(f".net salvo em {out_file}")

    def run(self):
        """
        Ponto de entrada principal para executar o processo de geração da netlist.
        """
        self.save_netlist()