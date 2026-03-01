import subprocess

from runner.config import RunnerSettings
from runner.doctor import evaluate_host_readiness


def test_doctor_ready_when_all_checks_pass(tmp_path, monkeypatch) -> None:
    app_dir = tmp_path / "Capture One.app"
    app_dir.mkdir()
    import_dir = tmp_path / "imports"

    monkeypatch.setattr("runner.doctor.shutil.which", lambda _: "/usr/bin/osascript")

    def fake_run(
        cmd: list[str],
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        assert cmd[:2] == ["osascript", "-e"]
        assert check is True
        assert capture_output is True
        assert text is True
        assert timeout == 5
        return subprocess.CompletedProcess(cmd, 0, stdout="com.captureone.captureone16\n")

    monkeypatch.setattr("runner.doctor.subprocess.run", fake_run)

    settings = RunnerSettings(
        execution_mode="host",
        captureone_app_path=str(app_dir),
        captureone_import_dir=str(import_dir),
    )
    report = evaluate_host_readiness(settings)
    assert report.ok is True
    assert report.captureone_app_exists is True
    assert report.osascript_available is True
    assert report.captureone_appleevent_ok is True
    assert report.import_dir_writable is True


def test_doctor_not_ready_when_capture_one_missing(tmp_path, monkeypatch) -> None:
    import_dir = tmp_path / "imports"
    monkeypatch.setattr("runner.doctor.shutil.which", lambda _: "/usr/bin/osascript")
    settings = RunnerSettings(
        execution_mode="host",
        captureone_app_path=str(tmp_path / "Missing Capture One.app"),
        captureone_import_dir=str(import_dir),
    )
    report = evaluate_host_readiness(settings)
    assert report.ok is False
    assert report.captureone_app_exists is False
