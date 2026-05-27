from pathlib import Path

from paper_distiller import ui_app
from paper_distiller.paths import KnowledgeBasePaths, PaperId
from paper_distiller.pdf import PaperPdfGroup
from paper_distiller.ui_core import collect_markdown_files, save_uploaded_pdfs, zip_markdown_files


class FakeUpload:
    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self._data = data

    def getbuffer(self) -> memoryview:
        return memoryview(self._data)


def test_save_uploaded_pdfs_ignores_non_pdf(tmp_path: Path) -> None:
    paths = KnowledgeBasePaths(tmp_path)
    uploads = [
        FakeUpload("paper.pdf", b"%PDF"),
        FakeUpload("notes.txt", b"not a pdf"),
    ]

    saved = save_uploaded_pdfs(uploads, paths, "A_core")

    assert saved == [tmp_path / "papers" / "raw" / "A_core" / "paper.pdf"]
    assert saved[0].read_bytes() == b"%PDF"
    assert not (tmp_path / "papers" / "raw" / "A_core" / "notes.txt").exists()


def test_collect_and_zip_markdown_files(tmp_path: Path) -> None:
    paths = KnowledgeBasePaths(tmp_path)
    output = tmp_path / "notes" / "literature" / "A_core" / "paper.md"
    output.parent.mkdir(parents=True)
    output.write_text("# Paper\n", encoding="utf-8")

    files = collect_markdown_files(paths)
    zipped = zip_markdown_files(files)

    assert [file.relative_path for file in files] == ["notes/literature/A_core/paper.md"]
    assert zipped.startswith(b"PK")


def test_ui_extract_all_processes_only_selected_category(
    tmp_path: Path,
    monkeypatch,
) -> None:
    paths = KnowledgeBasePaths(tmp_path)
    groups = [
        PaperPdfGroup(PaperId(category="A_core", stem="core"), pdfs=(), has_supplement=False),
        PaperPdfGroup(
            PaperId(category="B_related", stem="related"),
            pdfs=(),
            has_supplement=False,
        ),
    ]
    monkeypatch.setattr(ui_app, "scan_pdf_groups", lambda raw_dir: groups)
    monkeypatch.setattr(
        ui_app,
        "extract_group_text",
        lambda group: f"extracted {group.paper.category}/{group.paper.stem}",
    )

    done, skipped = ui_app._extract_all(paths, category="A_core")

    assert (done, skipped) == (1, 0)
    assert (tmp_path / "papers" / "text" / "A_core" / "core.txt").exists()
    assert not (tmp_path / "papers" / "text" / "B_related" / "related.txt").exists()
