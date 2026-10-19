import pytest
from pydantic import ValidationError

from wayfinder.settings import WebSettings


def test_web_settings_defaults_and_unlimited_caps() -> None:
    settings = WebSettings(_env_file=None)

    assert settings.session_idle_days == 7
    assert settings.session_absolute_days == 30
    assert settings.upload_max_mb == 10
    assert settings.vi_min_diacritic_ratio is None
    assert settings.build_max_pages is None
    assert settings.build_monthly_max is None
    assert settings.system_daily_build_max_usd is None
    assert settings.env == "dev"
    assert settings.mailer == "console"
    assert settings.cloudinary_folder == "wayfinder/dev"


def test_production_defaults_to_smtp_and_production_folder() -> None:
    settings = WebSettings(_env_file=None, env="prod")

    assert settings.mailer == "smtp"
    assert settings.cloudinary_folder == "wayfinder/prod"


@pytest.mark.parametrize("field", ["session_idle_days", "upload_max_mb", "signed_url_ttl_seconds", "page_image_width"])
def test_positive_fields_reject_zero(field: str) -> None:
    with pytest.raises(ValidationError):
        WebSettings(_env_file=None, **{field: 0})


def test_optional_limits_allow_none() -> None:
    settings = WebSettings(_env_file=None, build_monthly_max=None, build_max_pages=None)

    assert settings.build_monthly_max is None
    assert settings.build_max_pages is None


def test_optional_numeric_limits_parse_null_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("WAYFINDER_BUILD_MAX_PAGES", "null")
    monkeypatch.setenv("WAYFINDER_VI_MIN_DIACRITIC_RATIO", "null")
    monkeypatch.setenv("WAYFINDER_BUILD_MONTHLY_MAX", "none")
    monkeypatch.setenv("WAYFINDER_SYSTEM_DAILY_BUILD_MAX_USD", "")

    settings = WebSettings(_env_file=None)

    assert settings.build_max_pages is None
    assert settings.vi_min_diacritic_ratio is None
    assert settings.build_monthly_max is None
    assert settings.system_daily_build_max_usd is None
