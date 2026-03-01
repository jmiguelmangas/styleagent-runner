"""Host preflight diagnostics for runner desktop integrations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from collections.abc import Callable
from pathlib import Path
import json
import shutil
import subprocess

from runner.config import RunnerSettings


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    captureone_app_exists: bool
    osascript_available: bool
    captureone_appleevent_ok: bool
    import_dir_writable: bool
    details: dict[str, str]


def run_doctor(
    settings: RunnerSettings,
    *,
    emit: Callable[[str], None] = print,
) -> bool:
    report = evaluate_host_readiness(settings)
    emit(json.dumps(asdict(report), sort_keys=True))
    return report.ok


def evaluate_host_readiness(settings: RunnerSettings) -> DoctorReport:
    details: dict[str, str] = {}

    app_path = Path(settings.captureone_app_path).expanduser()
    captureone_app_exists = app_path.exists()
    details["captureone_app_path"] = str(app_path)

    osascript_path = shutil.which("osascript")
    osascript_available = osascript_path is not None
    if osascript_path:
        details["osascript_path"] = osascript_path

    import_dir = Path(settings.captureone_import_dir).expanduser()
    import_dir.mkdir(parents=True, exist_ok=True)
    probe = import_dir / ".doctor-write-test"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        import_dir_writable = True
    except OSError as exc:
        import_dir_writable = False
        details["import_dir_error"] = str(exc)
    details["import_dir"] = str(import_dir)

    captureone_appleevent_ok = False
    if captureone_app_exists and osascript_available:
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "Capture One" to id'],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            bundle_id = result.stdout.strip()
            captureone_appleevent_ok = bundle_id.startswith("com.captureone")
            details["captureone_bundle_id"] = bundle_id
        except (subprocess.SubprocessError, OSError) as exc:
            details["appleevent_error"] = str(exc)

    ok = (
        captureone_app_exists
        and osascript_available
        and captureone_appleevent_ok
        and import_dir_writable
    )

    return DoctorReport(
        ok=ok,
        captureone_app_exists=captureone_app_exists,
        osascript_available=osascript_available,
        captureone_appleevent_ok=captureone_appleevent_ok,
        import_dir_writable=import_dir_writable,
        details=details,
    )
