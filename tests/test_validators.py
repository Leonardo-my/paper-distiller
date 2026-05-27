from pathlib import Path

from paper_distiller.metadata import ensure_metadata_files, upsert_status
from paper_distiller.paths import KnowledgeBasePaths, PaperId
from paper_distiller.validators import check_kb


def test_check_detects_missing_reliability_label(tmp_path: Path) -> None:
    paths = KnowledgeBasePaths(tmp_path)
    paths.ensure_layout()
    ensure_metadata_files(paths.metadata_dir)
    paper = PaperId("A_core", "paper")
    upsert_status(paths.reading_status_csv, paper.raw_file_name, {"extracted": True})

    for output in [
        paths.literature_note(paper),
        paths.theorem_card(paper),
        paths.proof_card(paper),
        paths.writing_card(paper),
        paths.audit_report(paper),
    ]:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("# Title\n\nNo label here.\n", encoding="utf-8")

    issues = check_kb(paths)

    assert any("Missing Reliability" in issue.message for issue in issues)
