"""LLM backend adapters."""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Protocol

OPENAI_MODEL_ENV = "PAPER_DISTILLER_OPENAI_MODEL"


class LlmBackend(Protocol):
    def complete(self, prompt: str) -> str:
        """Return Markdown generated from a prompt."""


@dataclass
class OfflineBackend:
    target_name: str

    def complete(self, prompt: str) -> str:
        return (
            f"# TODO: {self.target_name}\n\n"
            "This scaffold was generated with the offline backend. Re-run with "
            "`--backend openai` or `--backend command`, or fill this file manually.\n\n"
            "## Reliability / Verification status\n\n"
            "needs PDF verification\n\n"
            "<details>\n<summary>Prompt used to generate this scaffold</summary>\n\n"
            "```text\n"
            f"{prompt[:12000]}\n"
            "```\n\n"
            "</details>\n"
        )


@dataclass
class CommandBackend:
    command: str

    def complete(self, prompt: str) -> str:
        args = shlex.split(self.command, posix=os.name != "nt")
        result = subprocess.run(
            args,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"LLM command failed with exit code {result.returncode}: {result.stderr}"
            )
        return result.stdout.strip()


@dataclass
class OpenAIBackend:
    model: str

    def complete(self, prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI backend requires the optional dependency: "
                'python -m pip install "paper-distiller[openai]"'
            ) from exc

        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            input=prompt,
        )
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text.strip()
        return str(response)


def build_backend(
    backend: str,
    target_name: str,
    model: str | None = None,
    llm_command: str | None = None,
) -> LlmBackend:
    if backend == "offline":
        return OfflineBackend(target_name=target_name)
    if backend == "command":
        if not llm_command:
            raise ValueError("--llm-command is required for the command backend")
        return CommandBackend(command=llm_command)
    if backend == "openai":
        resolved_model = model or os.environ.get(OPENAI_MODEL_ENV)
        if not resolved_model:
            raise ValueError(
                "OpenAI backend requires --model or the "
                f"{OPENAI_MODEL_ENV} environment variable"
            )
        return OpenAIBackend(model=resolved_model)
    raise ValueError(f"Unknown backend: {backend}")
