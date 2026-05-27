from pathlib import Path

from paper_distiller.paths import KnowledgeBasePaths
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
