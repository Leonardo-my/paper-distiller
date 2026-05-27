from paper_distiller.templates import list_package_presets, normalize_preset_name


def test_normalize_preset_name_accepts_cli_friendly_hyphen() -> None:
    assert normalize_preset_name("stat-transfer") == "stat_transfer"


def test_list_package_presets_includes_builtin_presets() -> None:
    presets = list_package_presets()

    assert "generic" in presets
    assert "stat-transfer" in presets
