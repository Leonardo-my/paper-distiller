from pathlib import Path

from paper_distiller.pdf import scan_pdf_groups


def test_scan_pdf_groups_pairs_supplement(tmp_path: Path) -> None:
    raw = tmp_path / "papers" / "raw"
    category = raw / "A_core"
    category.mkdir(parents=True)
    (category / "paper.pdf").write_bytes(b"%PDF-placeholder")
    (category / "paper_Supplement.pdf").write_bytes(b"%PDF-placeholder")
    (category / "other.pdf").write_bytes(b"%PDF-placeholder")

    groups = scan_pdf_groups(raw)

    by_stem = {group.paper.stem: group for group in groups}
    assert set(by_stem) == {"paper", "other"}
    assert by_stem["paper"].has_supplement is True
    assert len(by_stem["paper"].pdfs) == 2
    assert by_stem["other"].has_supplement is False
