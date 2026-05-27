from pathlib import Path

from paper_distiller.config import DistillationConfig, load_config, save_config


def test_config_round_trip_supports_chinese_profile(tmp_path: Path) -> None:
    path = tmp_path / "paper_distiller.toml"
    config = DistillationConfig(
        preset="generic",
        discipline="公共卫生",
        source_language="auto",
        output_language="zh",
        depth="deep",
        audience="graduate researcher",
        math_level="light",
    )

    save_config(path, config)

    loaded = load_config(path)
    assert loaded.discipline == "公共卫生"
    assert loaded.output_language == "zh"
    assert loaded.depth == "deep"
    assert "Simplified Chinese" in loaded.to_template_context()["language_instruction"]


def test_config_accepts_bilingual_language_alias() -> None:
    config = DistillationConfig(output_language="both").normalized()

    assert config.output_language == "bilingual"
