from paper_distiller.templates import (
    list_package_presets,
    normalize_preset_name,
    package_template_dir,
    render_template,
)


def test_normalize_preset_name_accepts_cli_friendly_hyphen() -> None:
    assert normalize_preset_name("stat-transfer") == "stat_transfer"


def test_list_package_presets_includes_builtin_presets() -> None:
    presets = list_package_presets()

    assert "generic" in presets
    assert "stat-transfer" in presets


def test_c_background_literature_prompt_requires_relevance_score() -> None:
    template = package_template_dir("stat-transfer") / "literature_note.md.j2"

    rendered = render_template(
        template,
        preset="stat-transfer",
        discipline="statistical transfer learning",
        audience="researcher",
        source_language="auto",
        output_language="en",
        depth="standard",
        math_level="heavy",
        language_instruction="",
        discipline_instruction="",
        depth_instruction="",
        math_instruction="",
        category="C_background",
        paper_text="Example paper text",
        stem="example",
    )

    assert "Relevance score" in rendered
    assert "keep the note short" in rendered
