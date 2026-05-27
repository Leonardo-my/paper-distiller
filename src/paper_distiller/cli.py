"""Command line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .config import DistillationConfig, load_config, save_config
from .constants import CATEGORIES
from .llm import build_backend
from .metadata import ensure_metadata_files, mark_human_verified, read_status, upsert_status
from .paths import KnowledgeBasePaths, PaperId
from .pdf import extract_group_text, scan_pdf_groups
from .pipeline import distill_paper
from .synthesis import generate_synthesis
from .templates import copy_preset_templates
from .validators import check_kb

app = typer.Typer(no_args_is_help=True, help="Distill research papers into Markdown notes.")
console = Console()


def _paths(root: Path) -> KnowledgeBasePaths:
    return KnowledgeBasePaths(root=root.resolve())


def _validate_category(category: str) -> str:
    if category not in CATEGORIES:
        raise typer.BadParameter(f"category must be one of: {', '.join(CATEGORIES)}")
    return category


def _load_profile(
    paths: KnowledgeBasePaths,
    *,
    preset: str | None = None,
    discipline: str | None = None,
    source_language: str | None = None,
    output_language: str | None = None,
    depth: str | None = None,
    audience: str | None = None,
    math_level: str | None = None,
) -> DistillationConfig:
    try:
        return load_config(paths.config_file).with_overrides(
            preset=preset,
            discipline=discipline,
            source_language=source_language,
            output_language=output_language,
            depth=depth,
            audience=audience,
            math_level=math_level,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _extract_all(paths: KnowledgeBasePaths, force: bool = False) -> tuple[int, int]:
    paths.ensure_layout()
    ensure_metadata_files(paths.metadata_dir)
    groups = scan_pdf_groups(paths.raw_dir)
    done = 0
    skipped = 0
    for group in groups:
        text_path = paths.text_file(group.paper)
        if text_path.exists() and not force:
            skipped += 1
            continue
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(extract_group_text(group), encoding="utf-8")
        upsert_status(
            paths.reading_status_csv,
            group.paper.raw_file_name,
            {"extracted": True, "human_verified": False},
        )
        done += 1
    return done, skipped


def _find_extracted_papers(
    paths: KnowledgeBasePaths,
    category: str | None = None,
    limit: int | None = None,
) -> list[PaperId]:
    categories = [_validate_category(category)] if category else list(CATEGORIES)
    papers: list[PaperId] = []

    for current_category in categories:
        text_dir = paths.text_dir / current_category
        if not text_dir.exists():
            continue
        for text_file in sorted(text_dir.glob("*.txt")):
            papers.append(PaperId(category=current_category, stem=text_file.stem))

    if limit is not None:
        return papers[:limit]
    return papers


def _distill_many(
    paths: KnowledgeBasePaths,
    papers: list[PaperId],
    backend: str,
    model: str | None,
    llm_command: str | None,
    config: DistillationConfig,
    force: bool,
) -> int:
    total_written = 0
    for index, paper in enumerate(papers, start=1):
        console.print(f"[cyan][{index}/{len(papers)}][/cyan] {paper.category}/{paper.stem}")
        llm = build_backend(
            backend,
            target_name=f"{paper.category}/{paper.stem}",
            model=model,
            llm_command=llm_command,
        )
        written = distill_paper(paths, paper, llm, config=config, force=force)
        total_written += len(written)
    return total_written


@app.command()
def init(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory to create.")],
    preset: Annotated[str, typer.Option(help="Prompt preset to install.")] = "generic",
    discipline: Annotated[str, typer.Option(help="Discipline profile, e.g. biology.")] = "general",
    source_language: Annotated[str, typer.Option(help="auto, en, or zh.")] = "auto",
    output_language: Annotated[
        str,
        typer.Option(help="en, zh, bilingual, or same-as-source."),
    ] = "en",
    depth: Annotated[str, typer.Option(help="short, standard, or deep.")] = "standard",
    audience: Annotated[str, typer.Option(help="Target reader profile.")] = "researcher",
    math_level: Annotated[str, typer.Option(help="auto, none, light, or heavy.")] = "auto",
    force: Annotated[bool, typer.Option(help="Overwrite existing prompt templates.")] = False,
) -> None:
    """Create a knowledge-base layout and install prompt templates."""

    paths = _paths(root)
    paths.ensure_layout()
    ensure_metadata_files(paths.metadata_dir)
    try:
        config = DistillationConfig(
            preset=preset,
            discipline=discipline,
            source_language=source_language,
            output_language=output_language,
            depth=depth,
            audience=audience,
            math_level=math_level,
        ).normalized()
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    save_config(paths.config_file, config)
    copy_preset_templates(config.preset, paths.prompts_dir, force=force)
    console.print(f"[green]Initialized[/green] {paths.root}")
    console.print(
        f"[green]Profile[/green] preset={config.preset}, discipline={config.discipline}, "
        f"output_language={config.output_language}, depth={config.depth}, "
        f"math_level={config.math_level}"
    )


@app.command()
def extract(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")],
    force: Annotated[bool, typer.Option(help="Overwrite existing text files.")] = False,
) -> None:
    """Extract text from all PDFs under papers/raw."""

    paths = _paths(root)
    groups = scan_pdf_groups(paths.raw_dir)
    if not groups:
        console.print("[yellow]No PDFs found.[/yellow]")
        return

    done, skipped = _extract_all(paths, force=force)
    console.print(f"[green]Extracted[/green] {done} paper(s); skipped {skipped}.")


@app.command()
def distill(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")],
    category: Annotated[str, typer.Argument(help="A_core, B_related, or C_background.")],
    stem: Annotated[str, typer.Argument(help="Paper file stem without .pdf.")],
    backend: Annotated[str, typer.Option(help="offline, command, or openai.")] = "offline",
    model: Annotated[str | None, typer.Option(help="Model name for the openai backend.")] = None,
    llm_command: Annotated[
        str | None,
        typer.Option(help="Command for the command backend. Reads prompt from stdin."),
    ] = None,
    discipline: Annotated[str | None, typer.Option(help="Override project discipline.")] = None,
    source_language: Annotated[str | None, typer.Option(help="Override source language.")] = None,
    output_language: Annotated[str | None, typer.Option(help="Override output language.")] = None,
    depth: Annotated[str | None, typer.Option(help="Override depth.")] = None,
    audience: Annotated[str | None, typer.Option(help="Override target reader profile.")] = None,
    math_level: Annotated[str | None, typer.Option(help="Override math level.")] = None,
    force: Annotated[bool, typer.Option(help="Overwrite existing output files.")] = False,
) -> None:
    """Generate Markdown outputs for one paper."""

    category = _validate_category(category)
    paths = _paths(root)
    ensure_metadata_files(paths.metadata_dir)
    config = _load_profile(
        paths,
        discipline=discipline,
        source_language=source_language,
        output_language=output_language,
        depth=depth,
        audience=audience,
        math_level=math_level,
    )
    paper = PaperId(category=category, stem=stem)
    llm = build_backend(
        backend,
        target_name=f"{category}/{stem}",
        model=model,
        llm_command=llm_command,
    )
    written = distill_paper(paths, paper, llm, config=config, force=force)
    for path in written:
        console.print(f"[green]Wrote[/green] {path}")
    if not written:
        console.print(
            "[yellow]No files written; use --force to overwrite existing outputs.[/yellow]"
        )


@app.command("distill-batch")
def distill_batch(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")],
    category: Annotated[
        str | None,
        typer.Option(help="Only process one category: A_core, B_related, or C_background."),
    ] = None,
    backend: Annotated[str, typer.Option(help="offline, command, or openai.")] = "offline",
    model: Annotated[str | None, typer.Option(help="Model name for the openai backend.")] = None,
    llm_command: Annotated[
        str | None,
        typer.Option(help="Command for the command backend. Reads prompt from stdin."),
    ] = None,
    discipline: Annotated[str | None, typer.Option(help="Override project discipline.")] = None,
    source_language: Annotated[str | None, typer.Option(help="Override source language.")] = None,
    output_language: Annotated[str | None, typer.Option(help="Override output language.")] = None,
    depth: Annotated[str | None, typer.Option(help="Override depth.")] = None,
    audience: Annotated[str | None, typer.Option(help="Override target reader profile.")] = None,
    math_level: Annotated[str | None, typer.Option(help="Override math level.")] = None,
    force: Annotated[bool, typer.Option(help="Overwrite existing output files.")] = False,
    limit: Annotated[int | None, typer.Option(help="Maximum number of papers to process.")] = None,
    synthesize: Annotated[
        bool,
        typer.Option(help="Generate cross-paper synthesis files after distillation."),
    ] = False,
    batch_id: Annotated[str, typer.Option(help="Batch id for synthesis outputs.")] = "batch_01",
) -> None:
    """Generate Markdown outputs for all extracted text files."""

    paths = _paths(root)
    ensure_metadata_files(paths.metadata_dir)
    config = _load_profile(
        paths,
        discipline=discipline,
        source_language=source_language,
        output_language=output_language,
        depth=depth,
        audience=audience,
        math_level=math_level,
    )
    papers = _find_extracted_papers(paths, category=category, limit=limit)

    if not papers:
        console.print("[yellow]No extracted text files found.[/yellow]")
        return

    total_written = _distill_many(
        paths,
        papers,
        backend=backend,
        model=model,
        llm_command=llm_command,
        config=config,
        force=force,
    )
    console.print(f"[green]Batch complete.[/green] Wrote {total_written} file(s).")

    if synthesize:
        synthesis_category = category or "A_core"
        llm = build_backend(
            backend,
            target_name=f"synthesis/{batch_id}",
            model=model,
            llm_command=llm_command,
        )
        written = generate_synthesis(
            paths,
            batch_id=batch_id,
            category=synthesis_category,
            backend=llm,
            config=config,
            force=force,
        )
        for path in written:
            console.print(f"[green]Wrote synthesis[/green] {path}")


@app.command()
def synthesize(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")],
    batch_id: Annotated[str, typer.Argument(help="Example: batch_01")],
    category: Annotated[str, typer.Option(help="Category to synthesize.")] = "A_core",
    backend: Annotated[str, typer.Option(help="offline, command, or openai.")] = "offline",
    model: Annotated[str | None, typer.Option(help="Model name for the openai backend.")] = None,
    llm_command: Annotated[
        str | None,
        typer.Option(help="Command for the command backend. Reads prompt from stdin."),
    ] = None,
    discipline: Annotated[str | None, typer.Option(help="Override project discipline.")] = None,
    source_language: Annotated[str | None, typer.Option(help="Override source language.")] = None,
    output_language: Annotated[str | None, typer.Option(help="Override output language.")] = None,
    depth: Annotated[str | None, typer.Option(help="Override depth.")] = None,
    audience: Annotated[str | None, typer.Option(help="Override target reader profile.")] = None,
    math_level: Annotated[str | None, typer.Option(help="Override math level.")] = None,
    force: Annotated[bool, typer.Option(help="Overwrite existing synthesis files.")] = False,
) -> None:
    """Generate cross-paper synthesis files from existing notes."""

    category = _validate_category(category)
    paths = _paths(root)
    ensure_metadata_files(paths.metadata_dir)
    config = _load_profile(
        paths,
        discipline=discipline,
        source_language=source_language,
        output_language=output_language,
        depth=depth,
        audience=audience,
        math_level=math_level,
    )
    llm = build_backend(
        backend,
        target_name=f"synthesis/{batch_id}",
        model=model,
        llm_command=llm_command,
    )
    written = generate_synthesis(
        paths,
        batch_id=batch_id,
        category=category,
        backend=llm,
        config=config,
        force=force,
    )
    for path in written:
        console.print(f"[green]Wrote synthesis[/green] {path}")


@app.command()
def run(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")],
    category: Annotated[
        str | None,
        typer.Option(help="Only process one category: A_core, B_related, or C_background."),
    ] = None,
    preset: Annotated[str | None, typer.Option(help="Prompt preset to install/update.")] = None,
    backend: Annotated[str, typer.Option(help="offline, command, or openai.")] = "offline",
    model: Annotated[str | None, typer.Option(help="Model name for the openai backend.")] = None,
    llm_command: Annotated[
        str | None,
        typer.Option(help="Command for the command backend. Reads prompt from stdin."),
    ] = None,
    discipline: Annotated[str | None, typer.Option(help="Override project discipline.")] = None,
    source_language: Annotated[str | None, typer.Option(help="Override source language.")] = None,
    output_language: Annotated[str | None, typer.Option(help="Override output language.")] = None,
    depth: Annotated[str | None, typer.Option(help="Override depth.")] = None,
    audience: Annotated[str | None, typer.Option(help="Override target reader profile.")] = None,
    math_level: Annotated[str | None, typer.Option(help="Override math level.")] = None,
    force: Annotated[bool, typer.Option(help="Overwrite extracted/generated files.")] = False,
    synthesize: Annotated[
        bool,
        typer.Option(help="Generate cross-paper synthesis files after distillation."),
    ] = False,
    batch_id: Annotated[str, typer.Option(help="Batch id for synthesis outputs.")] = "batch_01",
    limit: Annotated[int | None, typer.Option(help="Maximum number of papers to process.")] = None,
) -> None:
    """Run init, extract, distill, optional synthesis, and structural checks."""

    paths = _paths(root)
    paths.ensure_layout()
    ensure_metadata_files(paths.metadata_dir)
    config = _load_profile(
        paths,
        preset=preset,
        discipline=discipline,
        source_language=source_language,
        output_language=output_language,
        depth=depth,
        audience=audience,
        math_level=math_level,
    )
    copy_preset_templates(config.preset, paths.prompts_dir, force=force)

    done, skipped = _extract_all(paths, force=force)
    console.print(f"[green]Extracted[/green] {done} paper(s); skipped {skipped}.")

    papers = _find_extracted_papers(paths, category=category, limit=limit)
    if not papers:
        console.print("[yellow]No extracted text files found.[/yellow]")
        return

    total_written = _distill_many(
        paths,
        papers,
        backend=backend,
        model=model,
        llm_command=llm_command,
        config=config,
        force=force,
    )
    console.print(f"[green]Distillation complete.[/green] Wrote {total_written} file(s).")

    if synthesize:
        synthesis_category = category or "A_core"
        llm = build_backend(
            backend,
            target_name=f"synthesis/{batch_id}",
            model=model,
            llm_command=llm_command,
        )
        written = generate_synthesis(
            paths,
            batch_id=batch_id,
            category=synthesis_category,
            backend=llm,
            config=config,
            force=force,
        )
        for path in written:
            console.print(f"[green]Wrote synthesis[/green] {path}")

    issues = check_kb(paths)
    if issues:
        console.print(
            "[yellow]Structural check found issues. Run `paper-distiller check`.[/yellow]"
        )
    else:
        console.print("[green]Structural check passed.[/green]")


@app.command()
def status(root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")]) -> None:
    """Show reading_status.csv."""

    paths = _paths(root)
    rows = read_status(paths.reading_status_csv)
    table = Table(title="Reading Status")
    fields = ["file_name", "extracted", "distilled", "audited", "human_verified", "revision_needed"]
    for field in fields:
        table.add_column(field)
    for row in rows:
        table.add_row(*(row.get(field, "") for field in fields))
    console.print(table)


@app.command(name="check")
def check_command(root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")]) -> None:
    """Run structural reliability checks."""

    paths = _paths(root)
    issues = check_kb(paths)
    if not issues:
        console.print("[green]No structural issues found.[/green]")
        return

    table = Table(title="Check Issues")
    table.add_column("Severity")
    table.add_column("Path")
    table.add_column("Message")
    for issue in issues:
        table.add_row(issue.severity, str(issue.path or ""), issue.message)
    console.print(table)
    raise typer.Exit(code=1)


@app.command("mark-verified")
def mark_verified(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")],
    file_name: Annotated[str, typer.Argument(help="Example: A_core/my-paper.pdf")],
) -> None:
    """Mark a paper as human verified after manual PDF checks."""

    paths = _paths(root)
    mark_human_verified(paths.reading_status_csv, file_name)
    console.print(f"[green]Marked human_verified=true[/green] for {file_name}")


if __name__ == "__main__":
    app()
