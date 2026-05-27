"""Project-level distillation configuration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 CI
    import tomli as tomllib  # type: ignore[no-redef]


LANGUAGE_ALIASES = {
    "auto": "auto",
    "automatic": "auto",
    "en": "en",
    "english": "en",
    "zh": "zh",
    "cn": "zh",
    "chinese": "zh",
    "zh-cn": "zh",
    "bilingual": "bilingual",
    "both": "bilingual",
    "same": "same-as-source",
    "same-as-source": "same-as-source",
}

DEPTH_VALUES = {"short", "standard", "deep"}
MATH_LEVEL_VALUES = {"auto", "none", "light", "heavy"}


@dataclass(frozen=True)
class DistillationConfig:
    """User-facing project profile for prompt rendering."""

    preset: str = "generic"
    discipline: str = "general"
    source_language: str = "auto"
    output_language: str = "en"
    depth: str = "standard"
    audience: str = "researcher"
    math_level: str = "auto"

    def normalized(self) -> DistillationConfig:
        return DistillationConfig(
            preset=self.preset,
            discipline=self.discipline or "general",
            source_language=normalize_language(self.source_language, allow_auto=True),
            output_language=normalize_language(
                self.output_language,
                allow_auto=False,
                allow_same=True,
                allow_bilingual=True,
            ),
            depth=normalize_choice(self.depth, DEPTH_VALUES, "depth"),
            audience=self.audience or "researcher",
            math_level=normalize_choice(self.math_level, MATH_LEVEL_VALUES, "math_level"),
        )

    def with_overrides(self, **overrides: str | None) -> DistillationConfig:
        values = {key: value for key, value in overrides.items() if value is not None}
        return replace(self, **values).normalized()

    def to_template_context(self) -> dict[str, str]:
        config = self.normalized()
        return {
            "preset": config.preset,
            "discipline": config.discipline,
            "source_language": config.source_language,
            "output_language": config.output_language,
            "depth": config.depth,
            "audience": config.audience,
            "math_level": config.math_level,
            "language_instruction": language_instruction(config),
            "discipline_instruction": discipline_instruction(config),
            "depth_instruction": depth_instruction(config),
            "math_instruction": math_instruction(config),
        }


def normalize_language(
    value: str,
    *,
    allow_auto: bool,
    allow_same: bool = False,
    allow_bilingual: bool = False,
) -> str:
    normalized = LANGUAGE_ALIASES.get(value.strip().lower())
    if normalized is None:
        raise ValueError(f"Unsupported language value: {value}")
    if normalized == "auto" and not allow_auto:
        raise ValueError("auto is only valid for source_language")
    if normalized == "same-as-source" and not allow_same:
        raise ValueError("same-as-source is only valid for output_language")
    if normalized == "bilingual" and not allow_bilingual:
        raise ValueError("bilingual is only valid for output_language")
    return normalized


def normalize_choice(value: str, allowed: set[str], field_name: str) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported {field_name}: {value}. Expected one of: {choices}")
    return normalized


def language_instruction(config: DistillationConfig) -> str:
    source = config.source_language
    output = config.output_language
    if output == "zh":
        output_rule = (
            "Write the Markdown output in Simplified Chinese; keep technical "
            "terms bilingual when useful."
        )
    elif output == "bilingual":
        output_rule = (
            "Write bilingual Markdown: main explanations in Simplified Chinese, with English "
            "technical terms, paper concepts, and theorem labels preserved."
        )
    elif output == "same-as-source":
        output_rule = "Write the output in the dominant language of the source paper."
    else:
        output_rule = "Write the Markdown output in English."
    return f"Source language: {source}. {output_rule}"


def discipline_instruction(config: DistillationConfig) -> str:
    return (
        f"Discipline: {config.discipline}. Adapt the extraction schema, terminology, "
        "evidence standards, and reusable insights to this discipline instead of assuming "
        "the paper is mathematical."
    )


def depth_instruction(config: DistillationConfig) -> str:
    if config.depth == "short":
        return "Depth: short. Prefer concise summaries and only the most reusable details."
    if config.depth == "deep":
        return (
            "Depth: deep. Capture methods, assumptions, evidence, limitations, and reusable "
            "writing patterns in detail."
        )
    return "Depth: standard. Balance concise summary with reusable research detail."


def math_instruction(config: DistillationConfig) -> str:
    if config.math_level == "none":
        return (
            "Math level: none. Do not force theorem/formula extraction when the "
            "paper is non-mathematical."
        )
    if config.math_level == "light":
        return "Math level: light. Extract key formulas only when central and reliable."
    if config.math_level == "heavy":
        return (
            "Math level: heavy. Preserve theorem, assumption, proof, and formula "
            "details carefully."
        )
    return (
        "Math level: auto. Match the paper: use theorem/formula extraction for mathematical "
        "papers, and evidence/method extraction for empirical or qualitative papers."
    )


def load_config(path: Path) -> DistillationConfig:
    if not path.exists():
        return DistillationConfig()
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("distillation", {})
    if not isinstance(section, dict):
        raise ValueError("paper_distiller.toml must contain a [distillation] table")
    return DistillationConfig(**_string_values(section)).normalized()


def save_config(path: Path, config: DistillationConfig) -> None:
    config = config.normalized()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "[distillation]",
                f"preset = {_toml_string(config.preset)}",
                f"discipline = {_toml_string(config.discipline)}",
                f"source_language = {_toml_string(config.source_language)}",
                f"output_language = {_toml_string(config.output_language)}",
                f"depth = {_toml_string(config.depth)}",
                f"audience = {_toml_string(config.audience)}",
                f"math_level = {_toml_string(config.math_level)}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _string_values(values: dict[str, Any]) -> dict[str, str]:
    allowed = set(DistillationConfig.__dataclass_fields__)
    return {key: str(value) for key, value in values.items() if key in allowed}


def _toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
