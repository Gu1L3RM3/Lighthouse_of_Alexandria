import json
from pathlib import Path

CELL = 64

def load_circuit(json_file='circuito.json'):
    with open(json_file, "r") as f:
        return json.load(f)

circuit_json=load_circuit()
lines=[]
lines.append("Version 4")
lines.append("SHEET 1 880 680")

def write_wires():
    for entity in circuit_json:
        if entity["entity_type"] ==  "Wire":
            start_pos =0 
            lines.append()

def save_path(out_file="circuit.asc"):
    Path(out_file).write_text("\n".join(lines), encoding="utf-8")
    print(f".asc salvo em {out_file}")

if __name__ == "__main__":
    out_file = "circuit.asc"
    data = load_circuit()
    write_wires(circuit_json)
    save_path(out_file)