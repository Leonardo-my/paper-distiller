from pathlib import Path

from paper_distiller.llm import OfflineBackend
from paper_distiller.paths import KnowledgeBasePaths, PaperId
from paper_distiller.synthesis import generate_synthesis
from paper_distiller.templates import copy_preset_templates


def test_generate_synthesis_writes_expected_batch_files(tmp_path: Path) -> None:
    paths = KnowledgeBasePaths(tmp_path)
    paths.ensure_layout()
    copy_preset_templates("stat-transfer", paths.prompts_dir)
    paper = PaperId("A_core", "paper")

    for output in [
        paths.literature_note(paper),
        paths.theorem_card(paper),
        paths.proof_card(paper),
        paths.writing_card(paper),
        paths.audit_report(paper),
    ]:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "# Source\n\nReliability / Verification status: clear\n",
            encoding="utf-8",
        )

    written = generate_synthesis(
        paths,
        batch_id="batch_01",
        category="A_core",
        backend=OfflineBackend(target_name="synthesis/batch_01"),
    )

    assert set(written) == {
        paths.batch_overview("batch_01"),
        paths.batch_theorem_comparison("batch_01"),
        paths.batch_assumption_map("batch_01"),
        paths.batch_proof_technique_map("batch_01"),
        paths.batch_gap_list("batch_01"),
        paths.batch_synthesis_audit("batch_01"),
    }
