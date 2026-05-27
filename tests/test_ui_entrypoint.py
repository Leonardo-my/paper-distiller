from pathlib import Path

from paper_distiller.ui import build_streamlit_command


def test_build_streamlit_command_binds_to_localhost_and_opens_browser() -> None:
    command = build_streamlit_command(Path("ui_app.py"), port=8765, headless=False)

    assert command[-4:] == [
        "--server.port=8765",
        "--server.address=localhost",
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
    ]


def test_build_streamlit_command_supports_headless_launch() -> None:
    command = build_streamlit_command(Path("ui_app.py"), port=8765, headless=True)

    assert "--server.headless=true" in command
