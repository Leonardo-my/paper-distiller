"""Command line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .constants import CATEGORIES
from .llm import build_backend
from .metadata import ensure_metadata_files, mark_human_verified, read_status, upsert_status
from .paths import KnowledgeBasePaths, PaperId
from .pdf import extract_group_text, scan_pdf_groups
from .pipeline import distill_paper
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


@app.command()
def init(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory to create.")],
    preset: Annotated[str, typer.Option(help="Prompt preset to install.")] = "stat_transfer",
    force: Annotated[bool, typer.Option(help="Overwrite existing prompt templates.")] = False,
) -> None:
    """Create a knowledge-base layout and install prompt templates."""

    paths = _paths(root)
    paths.ensure_layout()
    ensure_metadata_files(paths.metadata_dir)
    copy_preset_templates(preset, paths.prompts_dir, force=force)
    console.print(f"[green]Initialized[/green] {paths.root}")


@app.command()
def extract(
    root: Annotated[Path, typer.Argument(help="Knowledge-base directory.")],
    force: Annotated[bool, typer.Option(help="Overwrite existing text files.")] = False,
) -> None:
    """Extract text from all PDFs under papers/raw."""

    paths = _paths(root)
    paths.ensure_layout()
    ensure_metadata_files(paths.metadata_dir)
    groups = scan_pdf_groups(paths.raw_dir)
    if not groups:
        console.print("[yellow]No PDFs found.[/yellow]")
        return

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
    force: Annotated[bool, typer.Option(help="Overwrite existing output files.")] = False,
) -> None:
    """Generate Markdown outputs for one paper."""

    category = _validate_category(category)
    paths = _paths(root)
    ensure_metadata_files(paths.metadata_dir)
    paper = PaperId(category=category, stem=stem)
    llm = build_backend(
        backend,
        target_name=f"{category}/{stem}",
        model=model,
        llm_command=llm_command,
    )
    written = distill_paper(paths, paper, llm, force=force)
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
    force: Annotated[bool, typer.Option(help="Overwrite existing output files.")] = False,
    limit: Annotated[int | None, typer.Option(help="Maximum number of papers to process.")] = None,
) -> None:
    """Generate Markdown outputs for all extracted text files."""

    paths = _paths(root)
    ensure_metadata_files(paths.metadata_dir)
    categories = [_validate_category(category)] if category else list(CATEGORIES)
    papers: list[PaperId] = []

    for current_category in categories:
        text_dir = paths.text_dir / current_category
        if not text_dir.exists():
            continue
        for text_file in sorted(text_dir.glob("*.txt")):
            papers.append(PaperId(category=current_category, stem=text_file.stem))

    if limit is not None:
        papers = papers[:limit]

    if not papers:
        console.print("[yellow]No extracted text files found.[/yellow]")
        return

    total_written = 0
    for index, paper in enumerate(papers, start=1):
        console.print(f"[cyan][{index}/{len(papers)}][/cyan] {paper.category}/{paper.stem}")
        llm = build_backend(
            backend,
            target_name=f"{paper.category}/{paper.stem}",
            model=model,
            llm_command=llm_command,
        )
        written = distill_paper(paths, paper, llm, force=force)
        total_written += len(written)

    console.print(f"[green]Batch complete.[/green] Wrote {total_written} file(s).")


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
