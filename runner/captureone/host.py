"""Host integration helpers for Capture One desktop app."""

from __future__ import annotations

from pathlib import Path
import subprocess


def ensure_captureone_app_exists(app_path: str) -> Path:
    path = Path(app_path).expanduser()
    if not path.exists():
        raise RuntimeError(f"Capture One app not found: {path}")
    return path


def build_import_output_path(import_dir: str, artifact_id: str) -> Path:
    directory = Path(import_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{artifact_id}.costyle"


def open_costyle_in_captureone(
    *,
    app_path: str,
    costyle_path: Path,
    timeout_seconds: float,
) -> None:
    subprocess.run(
        ["open", "-a", app_path, str(costyle_path)],
        check=True,
        timeout=timeout_seconds,
    )
