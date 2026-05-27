"""PDF scanning and text extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .constants import CATEGORIES, SUPPLEMENT_SUFFIX
from .paths import PaperId


@dataclass(frozen=True)
class PaperPdfGroup:
    paper: PaperId
    pdfs: tuple[Path, ...]
    has_supplement: bool


def scan_pdf_groups(raw_dir: Path) -> list[PaperPdfGroup]:
    """Scan papers/raw and pair main PDFs with *_Supplement PDFs."""

    groups: list[PaperPdfGroup] = []
    for category in CATEGORIES:
        category_dir = raw_dir / category
        if not category_dir.exists():
            continue

        mains: dict[str, Path] = {}
        supplements: dict[str, Path] = {}
        for pdf_path in sorted(category_dir.glob("*.pdf")):
            stem = pdf_path.stem
            if stem.endswith(SUPPLEMENT_SUFFIX):
                supplements[stem[: -len(SUPPLEMENT_SUFFIX)]] = pdf_path
            else:
                mains[stem] = pdf_path

        for stem, main_path in sorted(mains.items()):
            pdfs = [main_path]
            supplement_path = supplements.pop(stem, None)
            if supplement_path is not None:
                pdfs.append(supplement_path)
            groups.append(
                PaperPdfGroup(
                    paper=PaperId(category=category, stem=stem),
                    pdfs=tuple(pdfs),
                    has_supplement=supplement_path is not None,
                )
            )

        for stem, supplement_path in sorted(supplements.items()):
            groups.append(
                PaperPdfGroup(
                    paper=PaperId(category=category, stem=stem),
                    pdfs=(supplement_path,),
                    has_supplement=True,
                )
            )

    return groups


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        parts.append(f"\n\n--- Page {index}: {pdf_path.name} ---\n\n{text}")
    return "".join(parts).strip()


def extract_group_text(group: PaperPdfGroup) -> str:
    parts = []
    for path in group.pdfs:
        label = "SUPPLEMENT" if path.stem.endswith(SUPPLEMENT_SUFFIX) else "MAIN"
        parts.append(f"\n\n========== {label}: {path.name} ==========\n\n")
        parts.append(extract_pdf_text(path))
    return "".join(parts).strip()
