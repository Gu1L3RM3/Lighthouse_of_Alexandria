from core.ecs import Entity
from core.managers.entity_manager import EntityManager
from core.settings import CELL_SIZE
from pathlib import Path
from core.components.connectable import Connectable
from core.components.label_component import LabelComponent
from core.components.position import Position
from entities.circuit_editor.eletric_components import *
class LtSpiceGenerate:
    def __init__(self,entity_manager:EntityManager):
        self.entity_manager=entity_manager
        self.lines=[]
        self.lines.append("Version 4")
        self.lines.append("SHEET 1 880 680")
        self.angles ={
            0:270,
            0:90,
            90:0,
            270:180,
            180:270
        }
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
            x, y = pos.x, pos.y

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
                        self.lines.append(f"WIRE {int(start[0])} {int(start[1])} {int(end[0])} {int(end[1])}")
                        drawn_wires.add((start, end))

    def write_resistors(self):
        """
        Gera os símbolos de resistores no arquivo .asc com suas posições e labels.
        """
        resistors = self.entity_manager.get_entities_by_class(Resistor)

        for r in resistors:
            pos: Position = r.get(Position)
            label: LabelComponent = r.get(LabelComponent)

            spr:Sprite=r.get(Sprite)

            x, y = int(pos.x), int(pos.y)

            angle =int(self.angles[spr.angle])
                
            if angle == 0 or angle == 180:
                
                self.lines.append(f"WIRE {x+16} {y} {x+16} {y+16}")
                self.lines.append(f"WIRE {x+16} {spr.rect.bottom-32} {x+16} {spr.rect.bottom+4}")
            # Símbolo do LTspice
            self.lines.append(f"SYMBOL res {x+78} {y-16} R{angle}")
            
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

            if angle == 270 or angle==90:
                self.lines.append(f"WIRE {x} {y} {x+16} {y}")
                self.lines.append(f"WIRE {spr.rect.right-32} {y} {spr.rect.right+4} {y}")
            if angle == 0 or angle == 180:
                self.lines.append(f"WIRE {x} {y} {x} {y+16}")
                self.lines.append(f"WIRE {x} {spr.rect.bottom-32} {x} {spr.rect.bottom+4}")

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

        for i in currents:
            pos: Position = i.get(Position)
            label: LabelComponent = i.get(LabelComponent)

            x, y = int(pos.x), int(pos.y)

            spr:Sprite=i.get(Sprite)

            angle =int(self.angles[spr.angle])

            if angle == 270 or angle == 90:
                self.lines.append(f"WIRE {x} {y} {x+16} {y}")
                self.lines.append(f"WIRE {spr.rect.right-32} {y} {spr.rect.right+4} {y}")
            if angle == 0 or angle ==180:
                self.lines.append(f"WIRE {x} {y} {x} {y+16}")
                self.lines.append(f"WIRE {x} {spr.rect.bottom-64} {x} {spr.rect.bottom+4}")


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
                
                # O ponto onde o FLAG é inserido se torna o nó de terra (net '0').
                # O LTspice exibirá o símbolo de terra nesse ponto.
                self.lines.append(f"FLAG {x} {y} 0")
    def generate_netlist(self):
        """
        Converte self.lines (já preenchido pelo .asc) em um netlist SPICE (.net).
        Faz parsing básico de WIRE, SYMBOL, FLAG e SYMATTR.
        """
        wires = []
        symbols = []
        flags = {}
        inst_attrs = {}
        current_inst = None

        # Parse básico das linhas já geradas
        for line in self.lines:
            parts = line.strip().split()

            if not parts:
                continue

            if parts[0] == "WIRE":
                # WIRE x1 y1 x2 y2
                x1, y1, x2, y2 = map(int, parts[1:])
                wires.append(((x1, y1), (x2, y2)))

            elif parts[0] == "FLAG":
                # FLAG x y netname
                x, y, net = int(parts[1]), int(parts[2]), parts[3]
                flags[(x, y)] = net

            elif parts[0] == "SYMBOL":
                # SYMBOL tipo x y R<ângulo>
                sym_type, x, y = parts[1], int(parts[2]), int(parts[3])
                current_inst = {"type": sym_type, "pos": (x, y), "attrs": {}}
                symbols.append(current_inst)

            elif parts[0] == "SYMATTR" and current_inst:
                # SYMATTR InstName R1
                key, value = parts[1], " ".join(parts[2:])
                current_inst["attrs"][key] = value

        # ===== Resolver conexões em nets =====
        # Cada posição é um nó -> vamos dar nomes (N001, N002, ...) se não tiver FLAG
        node_map = {}
        node_counter = 1

        def get_netname(pos):
            nonlocal node_counter
            if pos in flags:
                return flags[pos]
            if pos not in node_map:
                node_map[pos] = f"N{node_counter:03d}"
                node_counter += 1
            return node_map[pos]

        # Resolver conexões pelos wires
        connections = {}
        for (a, b) in wires:
            na, nb = get_netname(a), get_netname(b)
            connections.setdefault(a, set()).add(nb)
            connections.setdefault(b, set()).add(na)

        # ===== Montar netlist dos componentes =====
        netlist_lines = []
        for sym in symbols:
            inst_name = sym["attrs"].get("InstName", None)
            value = sym["attrs"].get("Value", "")

            if not inst_name:
                continue  # ignorar sem nome

            # Posição central do símbolo = definir pino
            pos = sym["pos"]
            n1 = get_netname(pos)
            # Para simplificação, ligamos sempre a dois nós (pino positivo e negativo fictício)
            # Em implementação mais avançada, você pode mapear pinos específicos de cada símbolo
            n2 = "0" if "voltage" in sym["type"] or "current" in sym["type"] else get_netname((pos[0]+16, pos[1]))

            line = f"{inst_name} {n1} {n2} {value}"
            netlist_lines.append(line)

        return netlist_lines

    def save_netlist(self, out_file="circuitoo.net"):
        netlist = self.generate_netlist()
        Path(out_file).write_text("\n".join(netlist), encoding="utf-8")
        print(f".net salvo em {out_file}")

    def save_path(self,out_file="circuit.asc"):
        Path(out_file).write_text("\n".join(self.lines), encoding="utf-8")
        print(f".asc salvo em {out_file}")
    def run(self):
        self.write_wires()
        self.write_wires_from_nodes()
        self.write_resistors()
        self.write_voltage_sources()
        self.write_current_sources()
        self.write_gnd()
        self.save_path()
        self.generate_netlist()
        self.save_netlist()