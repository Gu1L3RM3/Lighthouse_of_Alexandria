import json
from collections import deque
from pathlib import Path

from core.components.position import Position
from core.components.connectable import Connectable
from core.components.sprite import Sprite
from core.components.label_component import LabelComponent
from core.managers.entity_manager import EntityManager
from entities.circuit_editor.eletric_components import *

# Constante para o tamanho da célula da grade, inferido do JSON
CELL_SIZE = 64

class LtSpiceGenerate:
    """
    Gera uma netlist SPICE a partir de um arquivo de descrição de circuito em JSON.
    Esta classe é autônoma e processa diretamente a estrutura de dados do JSON.
    """
    def __init__(self, json_filepath: str,entity_manager:EntityManager):

        try:
            json_content_string = Path(json_filepath).read_text(encoding="utf-8")
            self.circuit_data = json.loads(json_content_string)
        except FileNotFoundError:
            print(f"ERRO: O arquivo de circuito '{json_filepath}' não foi encontrado.")
            self.circuit_data = [] # Inicializa com dados vazios para evitar mais erros
        except json.JSONDecodeError as e:
            print(f"ERRO: O arquivo '{json_filepath}' não contém um JSON válido. {e}")
            self.circuit_data = []
        self.entity_manager = entity_manager
        self.lines = []
        self.lines.append("Version 4")
        self.lines.append("SHEET 1 880 680")
        self.angles = {0: 90, 90: 0, 180: 270, 270: 180}
        self.angles_current = {0: 270, 90: 180, 180: 90, 270: 0}


    # --- Métodos de Geração .asc (sem alterações) ---
    def write_wires(self):
        wires =  self.entity_manager.get_entities_by_class(Wire)
        for wire in wires:
            conn:Connectable = wire.get(Connectable)
            pos:Position = wire.get(Position)
            start = (0,0)
            end = (0,0)
            if {"top","bottom"}.issubset(conn.base_connections):
                start = (pos.x, pos.y - CELL_SIZE)
                end   = (pos.x, pos.y + CELL_SIZE)
            if {"right","left"}.issubset(conn.base_connections):
                start = (pos.x-CELL_SIZE, pos.y )
                end   = (pos.x+CELL_SIZE, pos.y )
            
            self.lines.append(f"WIRE {int(start[0])} {int(start[1])} {int(end[0])} {int(end[1])}")
    def write_wires_from_nodes(self):
        """
        Gera wires automaticamente conectando todos os Connectables adjacentes,
        incluindo nodes, wires e componentes eletricos.
        """
        # Coletar todos entities que possuem Connectable
        all_connectables = []
        for cls in [Node, Wire, Resistor, VoutageSource, CurrentSource, Ground]:
            all_connectables += self.entity_manager.get_entities_by_class(cls)

        # Criar mapa de posição -> entity
        pos_map = {}
        for ent in all_connectables:
            pos: Position = ent.get(Position)
            pos_map[(pos.x, pos.y)] = ent

        drawn_wires = set()

        for ent in all_connectables:
            pos: Position = ent.get(Position)
            conn: Connectable = ent.get(Connectable)
            x, y = int(pos.x),int( pos.y)

            for direction in conn.base_connections:
                # calcula coordenada do vizinho
                if direction == "up":
                    neighbor_pos = (x, y - CELL_SIZE)
                elif direction == "down":
                    neighbor_pos = (x, y + CELL_SIZE)
                elif direction == "left":
                    neighbor_pos = (x - CELL_SIZE, y)
                elif direction == "right":
                    neighbor_pos = (x + CELL_SIZE, y)
                else:
                    continue

                # se existe vizinho nessa posição
                if neighbor_pos in pos_map:
                    # ordem consistente (para não duplicar wires)
                    start, end = sorted([(x, y), neighbor_pos])
                    if (start, end) not in drawn_wires:
                        self.lines.append(f"WIRE {start[0]} {start[1]} {end[0]} {end[1]}")
                        drawn_wires.add((start, end))

    def write_resistors(self):
        """
        Gera os símbolos de resistores no arquivo .asc com suas posições e labels.
        """
        resistors = self.entity_manager.get_entities_by_class(Resistor)
        offset = 16

        for r in resistors:
            pos: Position = r.get(Position)
            label: LabelComponent = r.get(LabelComponent)

            spr:Sprite=r.get(Sprite)

            x, y = int(pos.x), int(pos.y)

            angle =int(self.angles[spr.angle])
            if angle == 0 :
                x-=offset
                start_y=y+100
                
                self.lines.append(f"WIRE {x+offset} {y+16} {x+offset} {y-12}")
                self.lines.append(f"WIRE {x+offset} {start_y+28} {x+offset} {start_y-4}")
            if angle == 270:
                y+=offset
                start_x=x+100
                self.lines.append(f"WIRE {x+16} {y-offset} {x-12} {y-offset}")
                self.lines.append(f"WIRE {start_x+28} {y-offset} {start_x-4} {y-offset}")


            if angle == 90:
                y-=offset
                x+=96
                start_x = x - 100
                self.lines.append(f"WIRE {x-16} {y+offset} {x+57} {y+offset}")
                self.lines.append(f"WIRE {start_x-14} {y+offset} {start_x+2} {y+offset}")

            if angle == 180:
                x+=offset
                y+=115
                start_y=y-100
                self.lines.append(f"WIRE {x-offset} {y-16} {x-offset} {y+12}")
                self.lines.append(f"WIRE {x-offset} {start_y-28} {x-offset} {start_y+4}")


            # Símbolo do LTspice
            self.lines.append(f"SYMBOL res {x} {y} R{angle}")

            
            # Nome do resistor (InstName)
            if label and hasattr(label, "name"):
                self.lines.append(f"SYMATTR InstName {label.name}")

            # Valor do resistor
            if label and hasattr(label, "value"):
                self.lines.append(f"SYMATTR Value {label.value}")
    def write_voltage_sources(self):
        """
        Gera os símbolos de fontes de tensão no arquivo .asc com suas posições e labels.
        """
        voltages = self.entity_manager.get_entities_by_class(VoutageSource)

        for v in voltages:
            pos: Position = v.get(Position)
            label: LabelComponent = v.get(LabelComponent)

            x, y = int(pos.x), int(pos.y)

            spr:Sprite = v.get(Sprite)

            angle =int(self.angles[spr.angle])

            if angle == 0 :
                start_y=y+100
                
                self.lines.append(f"WIRE {x} {y+16} {x} {y-12}")
                self.lines.append(f"WIRE {x} {start_y+28} {x} {start_y-4}")
            if angle == 270:
                
                start_x=x+100
                self.lines.append(f"WIRE {x+16} {y} {x-12} {y}")
                self.lines.append(f"WIRE {start_x+28} {y} {start_x-4} {y}")


            if angle == 90:
                start_x=x-100
                self.lines.append(f"WIRE {x-16} {y} {x+12} {y}")
                self.lines.append(f"WIRE {start_x-28} {y} {start_x+4} {y}")

            if angle == 180:
                y+=115
                start_y=y-100
                
                self.lines.append(f"WIRE {x} {y-16} {x} {y+12}")
                self.lines.append(f"WIRE {x} {start_y-28} {x} {start_y+4}")

            # Símbolo do LTspice
            self.lines.append(f"SYMBOL voltage {x} {y} R{angle}")

            # Nome da fonte (InstName)
            if label and hasattr(label, "name"):
                self.lines.append(f"SYMATTR InstName {label.name}")

            # Valor da fonte
            if label and hasattr(label, "value"):
                self.lines.append(f"SYMATTR Value {label.value}")


    def write_current_sources(self):
        """
        Gera os símbolos de fontes de corrente no arquivo .asc com suas posições e labels.
        """
        currents = self.entity_manager.get_entities_by_class(CurrentSource)
        offset= 90
        for i in currents:
            pos: Position = i.get(Position)
            label: LabelComponent = i.get(LabelComponent)

            x, y = int(pos.x), int(pos.y)

            spr:Sprite=i.get(Sprite)

            angle =int(self.angles_current[spr.angle])
            print(angle)
            if angle == 0 :
                
                start_y=y+130
                self.lines.append(f"WIRE {x} {y} {x} {y-40}")
                self.lines.append(f"WIRE {x} {start_y} {x} {start_y-50}")
            if angle == 270:
                
                start_x=x+120
                self.lines.append(f"WIRE {x} {y} {x-40} {y}")
                self.lines.append(f"WIRE {start_x+10} {y} {start_x-60} {y}")

            if angle == 90:
                x+=10

                x+=offset
                start_x=x+10
                self.lines.append(f"WIRE {x+10} {y} {x-102} {y}")
                self.lines.append(f"WIRE {start_x+20} {y} {x} {y}")
            if angle == 180:
                y+=offset
                start_y=y-120
                self.lines.append(f"WIRE {x} {y} {x} {y+40}")
                self.lines.append(f"WIRE {x} {start_y} {x} {start_y+40}")
            # Símbolo do LTspice
            self.lines.append(f"SYMBOL current {x} {y} R{angle}")

            # Nome da fonte (InstName)
            if label and hasattr(label, "name"):
                self.lines.append(f"SYMATTR InstName {label.name}")

            # Valor da fonte
            if label and hasattr(label, "value"):
                self.lines.append(f"SYMATTR Value {label.value}")
    def write_gnd(self):
            """
            Gera o rótulo de nó '0' (terra) para todas as entidades Ground.
            No LTspice, o terra é definido pelo FLAG '0', não por um SYMBOL.
            """
            grounds = self.entity_manager.get_entities_by_class(Ground)

            for gnd in grounds:
                pos: Position = gnd.get(Position)
                
                x, y = int(pos.x), int(pos.y)
                
                self.lines.append(f"FLAG {x} {y} 0")

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
            sprite=next((c for c in comp['components'] if c['type'] == 'Sprite'), None)
            if not label_comp: continue
            if not sprite :continue
            
            name = label_comp['name']
            value = label_comp['value']
            
            terminals = self._get_terminals(comp)
            node_names = [
                terminal_to_node.get((comp['id'], term_name))
                for term_name, _ in sorted(terminals.items())
            ]
            
            
            if len(node_names) == 2:
                if 'I' in name and sprite['angle']==270:
                    netlist_lines.append(f"{name} {node_names[1]} {node_names[0]} {value}")
                else:
                    netlist_lines.append(f"{name} {node_names[0]} {node_names[1]} {value}")
        return netlist_lines
        
    def save_netlist(self, out_file="circuito.net"):
        """Salva a netlist gerada em um arquivo."""
        netlist = self.generate_netlist()
        header = ["* Netlist gerada automaticamente a partir do circuit.json", ".tran 1", ""]
        content = "\n".join(header + netlist + ["", ".end"])
        Path(out_file).write_text(content, encoding="utf-8")
        print(f".net salvo em {out_file}")
    def save_asc(self, out_file="circuit.asc"):
        Path(out_file).write_text("\n".join(self.lines), encoding="utf-8")
        print(f".asc salvo em {out_file}")
    def run(self):
        """
        Ponto de entrada principal para executar o processo de geração da netlist.
        """
        self.write_resistors()
        self.write_current_sources()
        self.write_gnd()
        self.write_voltage_sources()
        self.write_wires_from_nodes()
        self.save_asc()
        self.save_netlist()