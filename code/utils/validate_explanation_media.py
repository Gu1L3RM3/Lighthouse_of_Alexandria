from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CODE_DIR = ROOT_DIR / "code"
ASSETS_DIR = ROOT_DIR / "assets"
MAPS_DIR = ASSETS_DIR / "maps" / "fases"
IMAGES_DIR = ASSETS_DIR / "images"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from core.localization.explanation_asset_audit import audit_explanation_assets  # noqa: E402
from scenes.fases.explanation_content import EXPLANATION_CONTENT  # noqa: E402


PHASE_MAP_FILES = {
    "exp_fase_3": MAPS_DIR / "exp_fase_3.tmx",
    "exp_fase_4": MAPS_DIR / "exp_fase_4.tmx",
    "exp_fase_5": MAPS_DIR / "exp_fase_5.tmx",
    "exp_fase_6": MAPS_DIR / "exp_fase_6.tmx",
    "exp_fase_7": MAPS_DIR / "exp_fase_7.tmx",
}


def split_dialogue_lines(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(";") if part.strip()]


def parse_dialogues_from_tmx(tmx_path: Path) -> dict[str, list[str]]:
    tree = ET.parse(tmx_path)
    root = tree.getroot()
    dialogues: dict[str, list[str]] = {}
    for obj in root.findall(".//object"):
        name = obj.get("name", "")
        if not re.fullmatch(r"dialog_\d+", name):
            continue
        value = ""
        for prop in obj.findall("./properties/property"):
            if prop.get("name") == "dialogo":
                value = prop.get("value", "")
                break
        dialogues[name] = split_dialogue_lines(value)
    return dialogues


def validate_phase(phase: str, tmx_path: Path, config: dict) -> list[str]:
    errors: list[str] = []
    if not tmx_path.exists():
        return [f"{phase}: mapa nao encontrado em {tmx_path}"]

    dialogues_by_name = parse_dialogues_from_tmx(tmx_path)
    if not dialogues_by_name:
        return [f"{phase}: nenhum dialogo encontrado no mapa."]

    for dialog_name, map_lines in dialogues_by_name.items():
        media = config.get(dialog_name)
        if media is None:
            errors.append(f"{phase}/{dialog_name}: sem configuracao de imagens.")
            continue

        images = list(media.get("images", []))
        captions = list(media.get("captions", []))
        if not images:
            errors.append(f"{phase}/{dialog_name}: lista de imagens vazia.")
            continue

        if len(images) != len(map_lines):
            errors.append(
                f"{phase}/{dialog_name}: {len(images)} imagens para {len(map_lines)} falas."
            )
        if captions and len(captions) != len(map_lines):
            errors.append(
                f"{phase}/{dialog_name}: {len(captions)} legendas para {len(map_lines)} falas."
            )

        for rel_path in images:
            full_path = IMAGES_DIR / rel_path
            if not full_path.exists():
                errors.append(f"{phase}/{dialog_name}: imagem ausente -> {rel_path}")

    for dialog_name in config.keys():
        if dialog_name not in dialogues_by_name:
            errors.append(f"{phase}/{dialog_name}: configurado, mas nao existe no mapa.")

    return errors


def validate_localized_assets(language: str, require_localized_images: bool) -> list[str]:
    issues = audit_explanation_assets(
        EXPLANATION_CONTENT,
        images_root=IMAGES_DIR,
        language=language,
        require_localized_images=require_localized_images,
    )
    return [issue.to_message() for issue in issues]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida midias das fases explicativas.")
    parser.add_argument(
        "--language",
        choices=("pt-BR", "en", "all"),
        default="all",
        help="Idioma a validar para os assets explicativos.",
    )
    parser.add_argument(
        "--require-english-assets",
        action="store_true",
        help="Falha se assets em ingles ainda estiverem usando fallback para _ptbr.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    all_errors: list[str] = []
    for phase, tmx_path in PHASE_MAP_FILES.items():
        config = EXPLANATION_CONTENT.get(phase, {})
        if not config:
            all_errors.append(f"{phase}: sem entrada em EXPLANATION_CONTENT.")
            continue
        all_errors.extend(validate_phase(phase, tmx_path, config))

    languages = ("pt-BR", "en") if args.language == "all" else (args.language,)
    for language in languages:
        require_localized = language == "en" and args.require_english_assets
        all_errors.extend(validate_localized_assets(language, require_localized))

    if all_errors:
        print("VALIDACAO FALHOU")
        for item in all_errors:
            print(f"- {item}")
        return 1

    print("VALIDACAO OK: explicacoes consistentes (falas, imagens e legendas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
