from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def expected_explanation_image_path(relative_path: str, language: str) -> str:
    if language == "en":
        return relative_path.replace("_ptbr/", "_en/", 1)
    return relative_path


@dataclass(frozen=True)
class ExplanationAssetIssue:
    phase: str
    dialogue_name: str
    kind: str
    asset_path: str
    detail: str

    def to_message(self) -> str:
        return f"{self.phase}/{self.dialogue_name}: {self.detail} -> {self.asset_path}"


@dataclass(frozen=True)
class ExplanationAssetExpectation:
    phase: str
    dialogue_name: str
    source_path: str
    expected_path: str
    localized_exists: bool
    source_exists: bool


def build_explanation_asset_expectations(
    explanation_content: dict[str, dict[str, dict[str, list[str]]]],
    images_root: str | Path,
    language: str,
) -> list[ExplanationAssetExpectation]:
    root = Path(images_root)
    expectations: list[ExplanationAssetExpectation] = []
    for phase, dialogues in explanation_content.items():
        for dialogue_name, entry in dialogues.items():
            seen_paths: set[tuple[str, str]] = set()
            for source_path in entry.get("images", []):
                expected_path = expected_explanation_image_path(source_path, language)
                dedupe_key = (source_path, expected_path)
                if dedupe_key in seen_paths:
                    continue
                seen_paths.add(dedupe_key)
                expectations.append(
                    ExplanationAssetExpectation(
                        phase=phase,
                        dialogue_name=dialogue_name,
                        source_path=source_path,
                        expected_path=expected_path,
                        localized_exists=(root / expected_path).exists(),
                        source_exists=(root / source_path).exists(),
                    )
                )
    return expectations


def audit_explanation_assets(
    explanation_content: dict[str, dict[str, dict[str, list[str]]]],
    images_root: str | Path,
    language: str,
    require_localized_images: bool = False,
) -> list[ExplanationAssetIssue]:
    issues: list[ExplanationAssetIssue] = []
    for item in build_explanation_asset_expectations(explanation_content, images_root, language):
        if not item.source_exists:
            issues.append(
                ExplanationAssetIssue(
                    phase=item.phase,
                    dialogue_name=item.dialogue_name,
                    kind="missing_source",
                    asset_path=item.source_path,
                    detail="imagem base ausente",
                )
            )
            continue

        if require_localized_images and not item.localized_exists:
            issues.append(
                ExplanationAssetIssue(
                    phase=item.phase,
                    dialogue_name=item.dialogue_name,
                    kind="missing_localized",
                    asset_path=item.expected_path,
                    detail=f"imagem localizada ausente para idioma {language}",
                )
            )

    return issues


def build_explanation_asset_manifest_lines(
    explanation_content: dict[str, dict[str, dict[str, list[str]]]],
    images_root: str | Path,
    language: str,
) -> list[str]:
    lines = [
        f"# Explanation Image Checklist ({language})",
        "",
        "Expected localized assets for explanatory phases.",
        "",
    ]
    current_phase = None
    for item in build_explanation_asset_expectations(explanation_content, images_root, language):
        if item.phase != current_phase:
            current_phase = item.phase
            lines.append(f"## {current_phase}")
        status = "OK" if item.localized_exists else "MISSING"
        lines.append(f"- [{status}] {item.expected_path}")
    lines.append("")
    return lines
