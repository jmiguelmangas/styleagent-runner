import pytest

from runner.config import RunnerSettings


def test_settings_defaults() -> None:
    settings = RunnerSettings.from_env({})
    assert settings.api_base_url == "http://localhost:8000"
    assert settings.api_key is None
    assert settings.http_timeout_seconds == 10.0
    assert settings.http_retries == 2


def test_settings_from_env_custom_values() -> None:
    settings = RunnerSettings.from_env(
        {
            "RUNNER_API_BASE_URL": "https://api.styleagent.local/",
            "RUNNER_API_KEY": "secret-token",
            "RUNNER_HTTP_TIMEOUT_SECONDS": "4.5",
            "RUNNER_HTTP_RETRIES": "5",
        }
    )
    assert settings.api_base_url == "https://api.styleagent.local"
    assert settings.api_key == "secret-token"
    assert settings.http_timeout_seconds == 4.5
    assert settings.http_retries == 5


def test_settings_invalid_retry_raises() -> None:
    with pytest.raises(ValueError, match="RUNNER_HTTP_RETRIES"):
        RunnerSettings.from_env({"RUNNER_HTTP_RETRIES": "-1"})

