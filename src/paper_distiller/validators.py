"""Structural checks for a distilled knowledge base."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .constants import Category
from .metadata import read_status
from .paths import KnowledgeBasePaths, PaperId


@dataclass(frozen=True)
class CheckIssue:
    severity: str
    path: Path | None
    message: str


def expected_outputs(paths: KnowledgeBasePaths, paper: PaperId) -> list[Path]:
    outputs = [paths.literature_note(paper), paths.audit_report(paper)]
    if paper.category in (Category.A_CORE.value, Category.B_RELATED.value):
        outputs.append(paths.theorem_card(paper))
    if paper.category == Category.A_CORE.value:
        outputs.extend([paths.proof_card(paper), paths.writing_card(paper)])
    return outputs


def check_kb(paths: KnowledgeBasePaths) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    rows = read_status(paths.reading_status_csv)

    for row in rows:
        file_name = row.get("file_name", "")
        if "/" not in file_name:
            issues.append(
                CheckIssue("major", paths.reading_status_csv, f"Bad file_name: {file_name}")
            )
            continue
        category, filename = file_name.split("/", 1)
        stem = filename.removesuffix(".pdf")
        paper = PaperId(category=category, stem=stem)

        if row.get("audited", "").lower() == "true" and not row.get("audit_file"):
            issues.append(
                CheckIssue(
                    "critical",
                    paths.reading_status_csv,
                    f"{file_name} is audited but audit_file is empty",
                )
            )

        if row.get("human_verified", "").lower() == "true" and row.get(
            "revision_needed", ""
        ).lower() == "true":
            issues.append(
                CheckIssue(
                    "major",
                    paths.reading_status_csv,
                    f"{file_name} is human_verified while revision_needed is still true",
                )
            )

        for output in expected_outputs(paths, paper):
            if not output.exists():
                issues.append(CheckIssue("major", output, "Expected output is missing"))
                continue
            text = output.read_text(encoding="utf-8", errors="replace")
            if "Reliability" not in text and "Verification status" not in text:
                issues.append(
                    CheckIssue(
                        "major",
                        output,
                        "Missing Reliability / Verification status label",
                    )
                )

    return issues
