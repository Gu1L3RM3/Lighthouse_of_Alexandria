import json
from collections import deque
from pathlib import Path

from core.components.position import Position
from core.components.connectable import Connectable
from core.components.sprite import Sprite
from core.components.label_component import LabelComponent
from core.managers.entity_manager import EntityManager
from entities.circuit_editor.eletric_components import *
from core.settings import CELL_SIZE


class LtSpiceGenerate:
    """
    Gera uma netlist SPICE a partir de um arquivo de descrição de circuito em JSON.
    Esta classe é autônoma e processa diretamente a estrutura de dados do JSON.
    """
    def __init__(self, json_filepath: str,net_filepath:str,lt_spice_filepath,entity_manager:EntityManager):
        self.net_filepath= net_filepath
        self.lt_spice_filepath=lt_spice_filepath
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

# ... (todo o resto da sua classe LtSpiceGenerate permanece o mesmo) ...

    def _get_terminals(self, entity: dict) -> dict[str, tuple[int, int]]:
        """
        Calcula as coordenadas dos terminais com nomes que representam a polaridade
        elétrica padrão, respeitando a orientação (rotação) do componente.
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

        # Terminais para componentes de 1 célula (nós, fios, terra)
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

        # Terminais para componentes de 2 células
        elif entity_type in ['Resistor', 'VoutageSource', 'CurrentSource']:
            
            # --- LÓGICA PARA COMPONENTES HORIZONTAIS ---
            if angle == 0: # Padrão
                left_terminal = (x, center_y)
                right_terminal = (x + 2 * CELL_SIZE, center_y)
                if entity_type == 'Resistor':      return {'p1': left_terminal, 'p2': right_terminal}
                if entity_type == 'VoutageSource': return {'neg': left_terminal, 'pos': right_terminal}
                if entity_type == 'CurrentSource': return {'from': left_terminal, 'to': right_terminal}

            elif angle == 180: # Girado 180 graus (invertido)
                left_terminal = (x, center_y)
                right_terminal = (x + 2 * CELL_SIZE, center_y)
                if entity_type == 'Resistor':      return {'p1': left_terminal, 'p2': right_terminal}
                # Polaridade invertida para as fontes!
                if entity_type == 'VoutageSource': return {'pos': left_terminal, 'neg': right_terminal}
                if entity_type == 'CurrentSource': return {'to': left_terminal, 'from': right_terminal}

            # --- LÓGICA PARA COMPONENTES VERTICAIS ---
            elif angle == 90: # Padrão
                top_terminal = (center_x, y)
                bottom_terminal = (center_x, y + 2 * CELL_SIZE)
                if entity_type == 'Resistor':      return {'p1': top_terminal, 'p2': bottom_terminal}
                if entity_type == 'VoutageSource': return {'neg': top_terminal, 'pos': bottom_terminal}
                if entity_type == 'CurrentSource': return {'from': top_terminal, 'to': bottom_terminal}
            
            elif angle == 270: # Girado 180 graus (invertido)
                top_terminal = (center_x, y)
                bottom_terminal = (center_x, y + 2 * CELL_SIZE)
                if entity_type == 'Resistor':      return {'p1': top_terminal, 'p2': bottom_terminal}
                # Polaridade invertida para as fontes!
                if entity_type == 'VoutageSource': return {'pos': top_terminal, 'neg': bottom_terminal}
                if entity_type == 'CurrentSource': return {'to': top_terminal, 'from': bottom_terminal}
        
        return {}


    def generate_netlist(self) -> list[str]:
            """
            Executa a lógica principal de descoberta de nós e geração da netlist,
            respeitando a convenção de polaridade do SPICE.
            """
            if not self.circuit_data:
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
                if (entity_id, start_term_name) in visited_terminals: continue
                q = deque([(entity_id, start_term_name)])
                current_node_terminals = set()
                is_ground_node = False
                while q:
                    curr_id, curr_term_name = q.popleft()
                    if (curr_id, curr_term_name) in visited_terminals: continue
                    visited_terminals.add((curr_id, curr_term_name))
                    current_node_terminals.add((curr_id, curr_term_name))
                    curr_entity = self.circuit_data[curr_id]
                    if curr_entity['entity_type'] == 'Ground': is_ground_node = True
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
                comp_type = comp['entity_type']

                # Mapeia o nome do terminal para o nome do nó (ex: 'pos' -> 'N001')
                node_map = {
                    term_name: terminal_to_node.get((comp['id'], term_name))
                    for term_name in self._get_terminals(comp)
                }

                # Garante que todos os nós foram encontrados
                if not all(node_map.values()):
                    print(f"AVISO: Componente {name} tem nós desconectados. Pulando.")
                    continue

                # Aplica a regra de ordenação correta para cada tipo de componente
                if comp_type == 'VoutageSource':
                    # Convenção: V_nome <nó_positivo> <nó_negativo> <valor>
                    line = f"{name} {node_map['pos']} {node_map['neg']} {value}"
                    netlist_lines.append(line)
                
                elif comp_type == 'CurrentSource':
                    # Convenção: I_nome <nó_de_saída> <nó_de_entrada> <valor>
                    # (A corrente flui DE 'from' PARA 'to')
                    line = f"{name} {node_map['from']} {node_map['to']} {value}"
                    netlist_lines.append(line)

                elif comp_type == 'Resistor':
                    # Convenção: R_nome <nó_1> <nó_2> <valor>
                    # A corrente positiva flui de nó_1 para nó_2.
                    # A ordem p1, p2 é consistente (ex: cima->baixo, esquerda->direita)
                    line = f"{name} {node_map['p1']} {node_map['p2']} {value}"
                    netlist_lines.append(line)

            return netlist_lines
        
    def save_netlist(self ):
        """Salva a netlist gerada em um arquivo."""
        netlist = self.generate_netlist()
        header = ["* Netlist gerada automaticamente a partir do circuit.json", ".tran 1", ""]
        content = "\n".join(header + netlist + ["", ".end"])
        Path(self.net_filepath).write_text(content, encoding="utf-8")
        print(f".net salvo em {self.net_filepath}")
    def save_asc(self, ):
        Path(self.lt_spice_filepath).write_text("\n".join(self.lines), encoding="utf-8")
        print(f".asc salvo em {self.lt_spice_filepath}")
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