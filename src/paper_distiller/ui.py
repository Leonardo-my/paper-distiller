"""Console entry point for the local Streamlit UI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        import streamlit  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "The Web UI requires Streamlit. Install it with:\n"
            '  python -m pip install "paper-distiller[ui]"\n'
            'or for local development:\n'
            '  python -m pip install -e ".[ui]"'
        ) from exc

    app_path = Path(__file__).with_name("ui_app.py")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    raise SystemExit(subprocess.call(command, env=env))
