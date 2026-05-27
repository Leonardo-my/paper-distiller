"""Template loading and rendering."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def normalize_preset_name(preset: str) -> str:
    return preset.replace("-", "_")


def package_template_dir(preset: str) -> Path:
    return Path(str(files("paper_distiller") / "templates" / normalize_preset_name(preset)))


def copy_preset_templates(preset: str, destination: Path, force: bool = False) -> None:
    source = package_template_dir(preset)
    if not source.exists():
        raise ValueError(f"Unknown preset: {preset}")
    destination.mkdir(parents=True, exist_ok=True)

    for item in source.glob("*.md.j2"):
        target = destination / item.name.removesuffix(".j2")
        if target.exists() and not force:
            continue
        target.write_text(item.read_text(encoding="utf-8"), encoding="utf-8")


def render_template(template_path: Path, **context: object) -> str:
    environment = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = environment.get_template(template_path.name)
    return template.render(**context)
