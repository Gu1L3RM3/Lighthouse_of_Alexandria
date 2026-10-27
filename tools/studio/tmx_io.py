"""Read and write the parts of a Tiled .tmx map that the Level Studio edits.

Only tile layer data and object groups are rewritten; everything else in the XML is kept as is,
so the maps stay valid for Tiled and for pytmx.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

OBJECT_ATTRIBUTES = ("name", "type", "gid", "x", "y", "width", "height", "rotation")
SHAPE_TAGS = ("point", "ellipse", "polygon", "polyline", "text")
TILED_INDENT = " "


class TmxFormatError(ValueError):
    pass


def _number(raw: str | None):
    if raw is None:
        return None
    value = float(raw)
    return int(value) if value.is_integer() else value


def _format_number(value) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else repr(round(value, 4))


class TmxDocument:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        try:
            self.tree = ET.parse(self.path)
        except ET.ParseError as exc:
            raise TmxFormatError(f"{self.path}: {exc}") from exc
        self.root = self.tree.getroot()

    def to_dict(self) -> dict:
        root = self.root
        return {
            "width": int(root.get("width")),
            "height": int(root.get("height")),
            "tilewidth": int(root.get("tilewidth")),
            "tileheight": int(root.get("tileheight")),
            "nextobjectid": int(root.get("nextobjectid", "1")),
            "tilesets": [self._read_tileset(element) for element in root.findall("tileset")],
            "layers": [self._read_layer(element) for element in root.findall("layer")],
            "objectgroups": [self._read_group(element) for element in root.findall("objectgroup")],
        }

    def update(self, payload: dict) -> None:
        """Apply edited layers and object groups, matched by name."""
        layers = {layer["name"]: layer for layer in payload.get("layers", [])}
        for element in self.root.findall("layer"):
            if element.get("name") in layers:
                self._write_layer(element, layers[element.get("name")]["data"])

        groups = {group["name"]: group for group in payload.get("objectgroups", [])}
        for element in self.root.findall("objectgroup"):
            if element.get("name") in groups:
                self._write_group(element, groups[element.get("name")]["objects"])

    def save(self, path: str | Path | None = None) -> None:
        target = Path(path) if path else self.path
        ET.indent(self.tree, space=TILED_INDENT)
        # Match Tiled's own output so a save only shows real edits in git diffs.
        body = ET.tostring(self.root, encoding="unicode", short_empty_elements=True).replace(" />", "/>")
        target.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n{body}\n', encoding="utf-8")

    # tilesets -----------------------------------------------------------

    def _read_tileset(self, element: ET.Element) -> dict:
        image = element.find("image")
        return {
            "firstgid": int(element.get("firstgid")),
            "name": element.get("name", ""),
            "source": element.get("source", ""),
            "image": image.get("source") if image is not None else "",
            "imagewidth": int(image.get("width", 0)) if image is not None else 0,
            "imageheight": int(image.get("height", 0)) if image is not None else 0,
            "tilewidth": int(element.get("tilewidth", 0)),
            "tileheight": int(element.get("tileheight", 0)),
            "tilecount": int(element.get("tilecount", 0)),
            "columns": int(element.get("columns", 0)),
        }

    # tile layers --------------------------------------------------------

    def _read_layer(self, element: ET.Element) -> dict:
        data = element.find("data")
        if data is None or data.get("encoding") != "csv":
            raise TmxFormatError(f"{self.path}: layer {element.get('name')!r} is not CSV encoded; re-save it in Tiled with CSV")
        return {
            "id": int(element.get("id")),
            "name": element.get("name", ""),
            "width": int(element.get("width")),
            "height": int(element.get("height")),
            "data": [int(cell) for cell in (data.text or "").replace("\n", "").split(",") if cell.strip()],
        }

    def _write_layer(self, element: ET.Element, cells: list[int]) -> None:
        width = int(element.get("width"))
        height = int(element.get("height"))
        if len(cells) != width * height:
            raise TmxFormatError(f"layer {element.get('name')!r} needs {width * height} cells, got {len(cells)}")
        rows = [",".join(str(int(cell)) for cell in cells[row * width:(row + 1) * width]) for row in range(height)]
        element.find("data").text = "\n" + ",\n".join(rows) + "\n"

    # objects ------------------------------------------------------------

    def _read_group(self, element: ET.Element) -> dict:
        return {
            "id": int(element.get("id")),
            "name": element.get("name", ""),
            "objects": [self._read_object(obj) for obj in element.findall("object")],
        }

    def _read_object(self, element: ET.Element) -> dict:
        obj = {"id": int(element.get("id"))}
        for key in OBJECT_ATTRIBUTES:
            raw = element.get(key)
            if raw is None:
                continue
            obj[key] = raw if key in ("name", "type") else _number(raw)
        obj["shape"] = self._shape_of(element)
        properties = element.find("properties")
        obj["properties"] = [
            {
                "name": prop.get("name"),
                "type": prop.get("type", "string"),
                "value": prop.get("value") if prop.get("value") is not None else (prop.text or ""),
            }
            for prop in (properties.findall("property") if properties is not None else [])
        ]
        return obj

    @staticmethod
    def _shape_of(element: ET.Element) -> str:
        if element.get("gid") is not None:
            return "tile"
        for tag in SHAPE_TAGS:
            if element.find(tag) is not None:
                return tag
        return "rect"

    def _write_group(self, group: ET.Element, objects: list[dict]) -> None:
        existing = {int(obj.get("id")): obj for obj in group.findall("object")}
        for element in existing.values():
            group.remove(element)
        for obj in objects:
            element = existing.get(obj.get("id")) if obj.get("id") is not None else None
            if element is None:
                element = self._new_object_element(obj)
            self._write_object(element, obj)
            group.append(element)

    def _new_object_element(self, obj: dict) -> ET.Element:
        next_id = int(self.root.get("nextobjectid", "1"))
        self.root.set("nextobjectid", str(next_id + 1))
        obj["id"] = next_id
        element = ET.Element("object", {"id": str(next_id)})
        if obj.get("shape") in SHAPE_TAGS:
            ET.SubElement(element, obj["shape"])
        return element

    def _write_object(self, element: ET.Element, obj: dict) -> None:
        for key in OBJECT_ATTRIBUTES:
            value = obj.get(key)
            if value is None or value == "":
                element.attrib.pop(key, None)
            elif key in ("name", "type"):
                element.set(key, str(value))
            else:
                element.set(key, _format_number(value))
        # Tiled writes attributes as id, name, type, gid, x, y, width, height, rotation.
        ordered = {"id": element.get("id")}
        ordered.update((key, element.get(key)) for key in OBJECT_ATTRIBUTES if element.get(key) is not None)
        ordered.update(element.attrib)
        element.attrib.clear()
        element.attrib.update(ordered)
        self._write_properties(element, obj.get("properties", []))

    @staticmethod
    def _write_properties(element: ET.Element, properties: list[dict]) -> None:
        old = element.find("properties")
        if old is not None:
            element.remove(old)
        if not properties:
            return
        block = ET.Element("properties")
        for prop in properties:
            attrs = {"name": str(prop["name"])}
            if prop.get("type", "string") != "string":
                attrs["type"] = str(prop["type"])
            value = str(prop.get("value", ""))
            if "\n" in value:
                ET.SubElement(block, "property", attrs).text = value
            else:
                attrs["value"] = value
                ET.SubElement(block, "property", attrs)
        element.insert(0, block)
