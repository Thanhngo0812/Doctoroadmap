from pathlib import Path

from doc2roadmap.config import Settings


def test_example_lists_every_setting_and_keeps_api_key_empty() -> None:
    values = {}
    for line in Path(".env.example").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            name, value = line.split("=", 1)
            values[name] = value

    expected = {f"DOC2ROADMAP_{name.upper()}" for name in Settings.model_fields}
    assert set(values) == expected
    assert values["DOC2ROADMAP_GEMINI_API_KEY"] == ""


def test_api_key_is_a_redacted_secret() -> None:
    settings = Settings(_env_file=None, gemini_api_key="do-not-print")

    assert "do-not-print" not in repr(settings)
    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "do-not-print"


def test_few_shot_path_can_come_from_environment(tmp_path, monkeypatch) -> None:
    path = tmp_path / "few-shot.txt"
    monkeypatch.setenv("DOC2ROADMAP_EXTRACTION_FEW_SHOT", str(path))

    assert Settings(_env_file=None).extraction_few_shot == path

    monkeypatch.setenv("DOC2ROADMAP_EXTRACTION_FEW_SHOT", "")
    assert Settings(_env_file=None).extraction_few_shot is None
