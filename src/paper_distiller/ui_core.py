"""Helpers shared by the Streamlit UI and tests."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Protocol
from zipfile import ZIP_DEFLATED, ZipFile

from .constants import CATEGORIES
from .paths import KnowledgeBasePaths


class UploadedFileLike(Protocol):
    name: str

    def getbuffer(self) -> memoryview: ...


@dataclass(frozen=True)
class MarkdownFile:
    path: Path
    relative_path: str


def save_uploaded_pdfs(
    uploads: list[UploadedFileLike],
    paths: KnowledgeBasePaths,
    category: str,
) -> list[Path]:
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category}")

    target_dir = paths.raw_dir / category
    target_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for upload in uploads:
        if not upload.name.lower().endswith(".pdf"):
            continue
        target = target_dir / Path(upload.name).name
        target.write_bytes(bytes(upload.getbuffer()))
        saved.append(target)
    return saved


def collect_markdown_files(paths: KnowledgeBasePaths) -> list[MarkdownFile]:
    if not paths.notes_dir.exists():
        return []
    files: list[MarkdownFile] = []
    for path in sorted(paths.notes_dir.rglob("*.md")):
        files.append(
            MarkdownFile(
                path=path,
                relative_path=path.relative_to(paths.root).as_posix(),
            )
        )
    return files


def zip_markdown_files(files: list[MarkdownFile]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file.path, arcname=file.relative_path)
    return buffer.getvalue()


def write_bytes_to_file(source: BinaryIO, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read())
