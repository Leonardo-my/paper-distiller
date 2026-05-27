"""Path helpers for knowledge-base projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .constants import CATEGORIES, NOTE_DIRS, SUPPLEMENT_SUFFIX


@dataclass(frozen=True)
class PaperId:
    category: str
    stem: str

    @property
    def raw_file_name(self) -> str:
        return f"{self.category}/{self.stem}.pdf"

    @property
    def text_file_name(self) -> str:
        return f"{self.category}/{self.stem}.txt"


@dataclass(frozen=True)
class KnowledgeBasePaths:
    root: Path

    @property
    def raw_dir(self) -> Path:
        return self.root / "papers" / "raw"

    @property
    def text_dir(self) -> Path:
        return self.root / "papers" / "text"

    @property
    def notes_dir(self) -> Path:
        return self.root / "notes"

    @property
    def metadata_dir(self) -> Path:
        return self.root / "metadata"

    @property
    def prompts_dir(self) -> Path:
        return self.root / "prompts"

    @property
    def reading_status_csv(self) -> Path:
        return self.metadata_dir / "reading_status.csv"

    @property
    def bibliography_csv(self) -> Path:
        return self.metadata_dir / "bibliography.csv"

    def raw_pdf(self, paper: PaperId) -> Path:
        return self.raw_dir / paper.category / f"{paper.stem}.pdf"

    def supplement_pdf(self, paper: PaperId) -> Path:
        return self.raw_dir / paper.category / f"{paper.stem}{SUPPLEMENT_SUFFIX}.pdf"

    def text_file(self, paper: PaperId) -> Path:
        return self.text_dir / paper.category / f"{paper.stem}.txt"

    def literature_note(self, paper: PaperId) -> Path:
        return self.notes_dir / "literature" / paper.category / f"{paper.stem}.md"

    def theorem_card(self, paper: PaperId) -> Path:
        return self.notes_dir / "theorem_cards" / paper.category / f"{paper.stem}-theorems.md"

    def proof_card(self, paper: PaperId) -> Path:
        return (
            self.notes_dir
            / "proof_cards"
            / paper.category
            / f"{paper.stem}-proof-techniques.md"
        )

    def writing_card(self, paper: PaperId) -> Path:
        return (
            self.notes_dir
            / "writing_patterns"
            / paper.category
            / f"{paper.stem}-writing-patterns.md"
        )

    def audit_report(self, paper: PaperId) -> Path:
        return self.notes_dir / "verification" / paper.category / f"{paper.stem}-audit.md"

    def ensure_layout(self) -> None:
        for base in (self.raw_dir, self.text_dir):
            for category in CATEGORIES:
                (base / category).mkdir(parents=True, exist_ok=True)

        for note_dir in NOTE_DIRS:
            for category in CATEGORIES:
                (self.notes_dir / note_dir / category).mkdir(parents=True, exist_ok=True)

        (self.notes_dir / "concept_cards").mkdir(parents=True, exist_ok=True)
        (self.notes_dir / "topic_maps" / "batches").mkdir(parents=True, exist_ok=True)
        (self.notes_dir / "research_gaps").mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
