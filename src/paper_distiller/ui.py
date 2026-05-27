"""Console entry point for the local Streamlit UI."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def build_streamlit_command(app_path: Path, *, port: int, headless: bool) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        f"--server.port={port}",
        "--server.address=localhost",
        f"--server.headless={'true' if headless else 'false'}",
        "--browser.gatherUsageStats=false",
    ]


def main(argv: list[str] | None = None) -> None:
    try:
        import streamlit  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "The Web UI requires Streamlit. Install it with:\n"
            '  python -m pip install "paper-distiller[ui]"\n'
            'or for local development:\n'
            '  python -m pip install -e ".[ui]"'
        ) from exc

    parser = argparse.ArgumentParser(description="Launch the local Paper Distiller Web UI.")
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Local port for the browser UI. Default: 8501.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Do not open a browser automatically.",
    )
    args = parser.parse_args(argv)

    app_path = Path(__file__).with_name("ui_app.py")
    command = build_streamlit_command(app_path, port=args.port, headless=args.headless)
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    raise SystemExit(subprocess.call(command, env=env))


if __name__ == "__main__":
    main()
