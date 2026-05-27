import pytest

from paper_distiller.llm import OPENAI_MODEL_ENV, OpenAIBackend, build_backend


def test_openai_backend_requires_explicit_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(OPENAI_MODEL_ENV, raising=False)

    with pytest.raises(ValueError, match=OPENAI_MODEL_ENV):
        build_backend("openai", target_name="A_core/paper")


def test_openai_backend_uses_model_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(OPENAI_MODEL_ENV, "test-model")

    backend = build_backend("openai", target_name="A_core/paper")

    assert isinstance(backend, OpenAIBackend)
    assert backend.model == "test-model"
