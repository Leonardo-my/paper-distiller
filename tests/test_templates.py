from paper_distiller.templates import normalize_preset_name


def test_normalize_preset_name_accepts_cli_friendly_hyphen() -> None:
    assert normalize_preset_name("stat-transfer") == "stat_transfer"
