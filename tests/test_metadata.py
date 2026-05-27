from pathlib import Path

import pytest

from paper_distiller.metadata import mark_human_verified, read_status, upsert_status


def test_upsert_status_does_not_auto_set_human_verified_true(tmp_path: Path) -> None:
    path = tmp_path / "reading_status.csv"

    with pytest.raises(ValueError):
        upsert_status(path, "A_core/paper.pdf", {"human_verified": True})


def test_mark_human_verified_is_explicit(tmp_path: Path) -> None:
    path = tmp_path / "reading_status.csv"
    upsert_status(path, "A_core/paper.pdf", {"extracted": True})

    mark_human_verified(path, "A_core/paper.pdf")

    rows = read_status(path)
    assert rows[0]["human_verified"] == "true"
