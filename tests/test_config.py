import pytest

from runner.config import RunnerSettings


def test_settings_defaults() -> None:
    settings = RunnerSettings.from_env({})
    assert settings.api_base_url == "http://localhost:8000"
    assert settings.poll_interval_seconds == 5.0
    assert settings.api_key is None
    assert settings.http_timeout_seconds == 10.0
    assert settings.http_retries == 2
    assert settings.execution_mode == "api"
    assert settings.captureone_app_path == "/Applications/Capture One.app"
    assert settings.captureone_auto_open is True
    assert settings.captureone_launch_mode == "auto"
    assert settings.captureone_cli_command == ""


def test_settings_from_env_custom_values() -> None:
    settings = RunnerSettings.from_env(
        {
            "RUNNER_API_BASE_URL": "https://api.styleagent.local/",
            "RUNNER_POLL_INTERVAL": "2.5",
            "RUNNER_API_KEY": "secret-token",
            "RUNNER_HTTP_TIMEOUT_SECONDS": "4.5",
            "RUNNER_HTTP_RETRIES": "5",
            "RUNNER_EXECUTION_MODE": "host",
            "RUNNER_CAPTUREONE_APP_PATH": "/Applications/Capture One.app",
            "RUNNER_CAPTUREONE_IMPORT_DIR": "/tmp/captureone-imports",
            "RUNNER_CAPTUREONE_OPEN_TIMEOUT_SECONDS": "20",
            "RUNNER_CAPTUREONE_AUTO_OPEN": "false",
            "RUNNER_CAPTUREONE_LAUNCH_MODE": "cli",
            "RUNNER_CAPTUREONE_CLI_COMMAND": "captureone-cli --import {costyle_path}",
        }
    )
    assert settings.api_base_url == "https://api.styleagent.local"
    assert settings.poll_interval_seconds == 2.5
    assert settings.api_key == "secret-token"
    assert settings.http_timeout_seconds == 4.5
    assert settings.http_retries == 5
    assert settings.execution_mode == "host"
    assert settings.captureone_app_path == "/Applications/Capture One.app"
    assert settings.captureone_import_dir == "/tmp/captureone-imports"
    assert settings.captureone_open_timeout_seconds == 20
    assert settings.captureone_auto_open is False
    assert settings.captureone_launch_mode == "cli"
    assert settings.captureone_cli_command == "captureone-cli --import {costyle_path}"


def test_settings_invalid_retry_raises() -> None:
    with pytest.raises(ValueError, match="RUNNER_HTTP_RETRIES"):
        RunnerSettings.from_env({"RUNNER_HTTP_RETRIES": "-1"})


def test_settings_invalid_poll_interval_raises() -> None:
    with pytest.raises(ValueError, match="RUNNER_POLL_INTERVAL"):
        RunnerSettings.from_env({"RUNNER_POLL_INTERVAL": "0"})


def test_settings_invalid_execution_mode_raises() -> None:
    with pytest.raises(ValueError, match="RUNNER_EXECUTION_MODE"):
        RunnerSettings.from_env({"RUNNER_EXECUTION_MODE": "desktop"})


def test_settings_invalid_captureone_launch_mode_raises() -> None:
    with pytest.raises(ValueError, match="RUNNER_CAPTUREONE_LAUNCH_MODE"):
        RunnerSettings.from_env({"RUNNER_CAPTUREONE_LAUNCH_MODE": "desktop"})
