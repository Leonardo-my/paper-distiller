"""Cross-paper synthesis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import DistillationConfig
from .llm import LlmBackend
from .paths import KnowledgeBasePaths
from .templates import render_template


@dataclass(frozen=True)
class SynthesisSpec:
    name: str
    prompt_file: str
    output_path: Path


def synthesis_specs(paths: KnowledgeBasePaths, batch_id: str) -> list[SynthesisSpec]:
    return [
        SynthesisSpec(
            name="batch overview",
            prompt_file="batch_overview.md",
            output_path=paths.batch_overview(batch_id),
        ),
        SynthesisSpec(
            name="theorem comparison",
            prompt_file="batch_theorem_comparison.md",
            output_path=paths.batch_theorem_comparison(batch_id),
        ),
        SynthesisSpec(
            name="assumption map",
            prompt_file="batch_assumption_map.md",
            output_path=paths.batch_assumption_map(batch_id),
        ),
        SynthesisSpec(
            name="proof technique map",
            prompt_file="batch_proof_technique_map.md",
            output_path=paths.batch_proof_technique_map(batch_id),
        ),
        SynthesisSpec(
            name="gap list",
            prompt_file="batch_gap_list.md",
            output_path=paths.batch_gap_list(batch_id),
        ),
        SynthesisSpec(
            name="synthesis audit",
            prompt_file="batch_synthesis_audit.md",
            output_path=paths.batch_synthesis_audit(batch_id),
        ),
    ]


def collect_synthesis_sources(
    paths: KnowledgeBasePaths,
    category: str,
    max_chars_per_file: int = 25000,
) -> dict[str, str]:
    """Collect generated single-paper notes for a category.

    Long files are truncated defensively because cross-paper prompts can become
    very large. The prompt asks the model to preserve uncertainty labels, so
    truncation is explicitly marked.
    """

    source_roots = [
        paths.notes_dir / "literature" / category,
        paths.notes_dir / "theorem_cards" / category,
        paths.notes_dir / "proof_cards" / category,
        paths.notes_dir / "writing_patterns" / category,
        paths.notes_dir / "verification" / category,
    ]
    collected: dict[str, str] = {}
    for root in source_roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md")):
            relative = path.relative_to(paths.root).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            if len(text) > max_chars_per_file:
                text = (
                    text[:max_chars_per_file]
                    + "\n\n[TRUNCATED BY PAPER DISTILLER: consult source file before citing.]\n"
                )
            collected[relative] = text
    return collected


def generate_synthesis(
    paths: KnowledgeBasePaths,
    batch_id: str,
    category: str,
    backend: LlmBackend,
    config: DistillationConfig | None = None,
    force: bool = False,
    max_chars_per_file: int = 25000,
) -> list[Path]:
    sources = collect_synthesis_sources(
        paths,
        category=category,
        max_chars_per_file=max_chars_per_file,
    )
    if not sources:
        raise FileNotFoundError(f"No generated Markdown notes found for category {category}")

    written: list[Path] = []
    generated_synthesis: dict[str, str] = {}
    prompt_profile = (config or DistillationConfig()).to_template_context()
    for spec in synthesis_specs(paths, batch_id):
        if spec.output_path.exists() and not force:
            generated_synthesis[spec.name] = spec.output_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            continue

        prompt_path = paths.prompts_dir / spec.prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"Missing synthesis prompt template: {prompt_path}")

        prompt = render_template(
            prompt_path,
            batch_id=batch_id,
            category=category,
            source_files=sources,
            generated_synthesis=generated_synthesis,
            **prompt_profile,
        )
        content = backend.complete(prompt)
        spec.output_path.parent.mkdir(parents=True, exist_ok=True)
        spec.output_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        generated_synthesis[spec.name] = content
        written.append(spec.output_path)

    return written
