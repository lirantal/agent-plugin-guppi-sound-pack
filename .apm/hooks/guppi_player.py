"""Play GUPPI CESP sounds in response to Codex lifecycle hooks."""

import json
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, TextIO

EVENT_CATEGORIES = {
    "SessionStart": "session.start",
    "UserPromptSubmit": "task.acknowledge",
    "PermissionRequest": "input.required",
    "PreCompact": "resource.limit",
    "Stop": "task.complete",
}


def event_category(event_name: str) -> str | None:
    """Return the CESP category for a supported Codex lifecycle event."""
    return EVENT_CATEGORIES.get(event_name)


def select_sound(
    manifest_path: Path, category: str, acknowledge: bool
) -> Path | None:
    """Choose an existing CESP sound for a category, if the category is enabled."""
    if category == "task.acknowledge" and not acknowledge:
        return None

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sounds = manifest.get("categories", {}).get(category, {}).get("sounds", [])
    candidates = [
        manifest_path.parent / sound["file"]
        for sound in sounds
        if isinstance(sound, dict) and isinstance(sound.get("file"), str)
    ]
    existing = [candidate for candidate in candidates if candidate.is_file()]
    return random.choice(existing) if existing else None


def _manifest_in(modules_directory: Path) -> Path | None:
    """Find this pack's CESP manifest in an APM package store."""
    if not modules_directory.is_dir():
        return None
    for manifest_path in modules_directory.rglob("openpeon.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("name") == "guppi":
            return manifest_path
    return None


def locate_manifest(
    payload: Mapping[str, object],
    runtime_path: Path | None = None,
    global_modules: Path | None = None,
) -> Path | None:
    """Locate canonical CESP assets beside source or in APM's package stores."""
    runtime = runtime_path or Path(__file__)
    for candidate in (runtime.with_name("openpeon.json"), runtime.parents[2] / "openpeon.json"):
        if candidate.is_file():
            return candidate

    workspaces = [Path.cwd()]
    cwd = payload.get("cwd")
    if isinstance(cwd, str):
        workspaces.insert(0, Path(cwd))
    for workspace in workspaces:
        for ancestor in (workspace, *workspace.parents):
            manifest_path = _manifest_in(ancestor / "apm_modules")
            if manifest_path is not None:
                return manifest_path

    return _manifest_in(global_modules or Path.home() / ".apm" / "apm_modules")


def play_sound(sound_path: Path, runner: Callable[..., object]) -> None:
    """Start macOS playback without holding up the Codex hook process."""
    runner(
        ["afplay", str(sound_path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def main(
    stdin: TextIO, environ: Mapping[str, str], runner: Callable[..., object]
) -> int:
    """Handle one Codex hook payload and always leave hook execution non-fatal."""
    try:
        payload = json.loads(stdin.read())
    except json.JSONDecodeError:
        return 0

    if not isinstance(payload, dict):
        return 0

    event_name = payload.get("hook_event_name")
    if not isinstance(event_name, str):
        return 0

    category = event_category(event_name)
    if category is None:
        return 0

    manifest_path = locate_manifest(payload)
    if manifest_path is None:
        return 0
    try:
        sound = select_sound(
            manifest_path,
            category,
            environ.get("GUPPI_ACKNOWLEDGE") == "1",
        )
    except (OSError, json.JSONDecodeError):
        return 0
    if sound is None:
        return 0

    try:
        play_sound(sound, runner)
    except OSError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.stdin, os.environ, subprocess.Popen))
