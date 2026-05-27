"""Distillation pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import DistillationConfig
from .constants import Category
from .llm import LlmBackend
from .metadata import upsert_status
from .paths import KnowledgeBasePaths, PaperId
from .templates import render_template


@dataclass(frozen=True)
class OutputSpec:
    name: str
    prompt_file: str
    output_path: Path
    status_updates: dict[str, str | bool]


def output_specs(paths: KnowledgeBasePaths, paper: PaperId) -> list[OutputSpec]:
    specs = [
        OutputSpec(
            name="literature note",
            prompt_file="literature_note.md",
            output_path=paths.literature_note(paper),
            status_updates={"distilled": True, "reviewed": True},
        )
    ]

    if paper.category in (Category.A_CORE.value, Category.B_RELATED.value):
        specs.append(
            OutputSpec(
                name="theorem card",
                prompt_file="theorem_card.md",
                output_path=paths.theorem_card(paper),
                status_updates={"theorem_extracted": True},
            )
        )

    if paper.category == Category.A_CORE.value:
        specs.extend(
            [
                OutputSpec(
                    name="proof card",
                    prompt_file="proof_card.md",
                    output_path=paths.proof_card(paper),
                    status_updates={"proof_extracted": True},
                ),
                OutputSpec(
                    name="writing-pattern card",
                    prompt_file="writing_patterns.md",
                    output_path=paths.writing_card(paper),
                    status_updates={},
                ),
            ]
        )

    specs.append(
        OutputSpec(
            name="audit report",
            prompt_file="audit_report.md",
            output_path=paths.audit_report(paper),
            status_updates={
                "audited": True,
                "audit_file": f"{paper.category}/{paper.stem}-audit.md",
                "revision_needed": True,
            },
        )
    )
    return specs


def distill_paper(
    paths: KnowledgeBasePaths,
    paper: PaperId,
    backend: LlmBackend,
    config: DistillationConfig | None = None,
    force: bool = False,
) -> list[Path]:
    text_path = paths.text_file(paper)
    if not text_path.exists():
        raise FileNotFoundError(f"Missing extracted text: {text_path}")

    paper_text = text_path.read_text(encoding="utf-8", errors="replace")
    written: list[Path] = []
    generated: dict[str, str] = {}
    prompt_profile = (config or DistillationConfig()).to_template_context()

    for spec in output_specs(paths, paper):
        if spec.output_path.exists() and not force:
            generated[spec.name] = spec.output_path.read_text(encoding="utf-8", errors="replace")
            continue

        prompt_path = paths.prompts_dir / spec.prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"Missing prompt template: {prompt_path}")

        prompt = render_template(
            prompt_path,
            category=paper.category,
            stem=paper.stem,
            paper_text=paper_text,
            generated_outputs=generated,
            **prompt_profile,
        )
        content = backend.complete(prompt)
        spec.output_path.parent.mkdir(parents=True, exist_ok=True)
        spec.output_path.write_text(content.rstrip() + "\n", encoding="utf-8")
        generated[spec.name] = content
        written.append(spec.output_path)

        upsert_status(
            paths.reading_status_csv,
            paper.raw_file_name,
            spec.status_updates,
        )

    return written
