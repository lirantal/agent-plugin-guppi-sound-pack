import importlib.util
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAYER_PATH = ROOT / ".apm" / "hooks" / "guppi_player.py"


def player_module():
    if not PLAYER_PATH.is_file():
        raise AssertionError("the deployed GUPPI hook runtime must exist")
    spec = importlib.util.spec_from_file_location("guppi_player", PLAYER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def event_category(event_name):
    return player_module().event_category(event_name)


def select_sound(category, acknowledge=False):
    player = player_module()
    if not hasattr(player, "select_sound"):
        raise AssertionError("guppi_player.select_sound must exist")
    return player.select_sound(ROOT / "openpeon.json", category, acknowledge)


def run_main(payload, environ, runner):
    player = player_module()
    if not hasattr(player, "main"):
        raise AssertionError("guppi_player.main must exist")
    return player.main(io.StringIO(payload), environ, runner)


def locate_manifest(payload, runtime_path, global_modules):
    player = player_module()
    if not hasattr(player, "locate_manifest"):
        raise AssertionError("guppi_player.locate_manifest must exist")
    return player.locate_manifest(payload, runtime_path, global_modules)


class EventCategoryTests(unittest.TestCase):
    def test_maps_supported_codex_events(self):
        self.assertEqual(event_category("SessionStart"), "session.start")
        self.assertEqual(event_category("PermissionRequest"), "input.required")
        self.assertEqual(event_category("PreCompact"), "resource.limit")
        self.assertEqual(event_category("Stop"), "task.complete")

    def test_unknown_event_is_silent(self):
        self.assertIsNone(event_category("PostToolUse"))


class SoundSelectionTests(unittest.TestCase):
    def test_selects_an_existing_manifest_sound(self):
        sound = select_sound("task.complete")

        self.assertIsNotNone(sound)
        self.assertTrue(sound.is_file())
        self.assertEqual(sound.suffix, ".wav")

    def test_acknowledgement_is_disabled_without_opt_in(self):
        self.assertIsNone(select_sound("task.acknowledge", acknowledge=False))

    def test_acknowledgement_selects_a_sound_when_opted_in(self):
        sound = select_sound("task.acknowledge", acknowledge=True)

        self.assertIsNotNone(sound)
        self.assertTrue(sound.is_file())


class ManifestLocationTests(unittest.TestCase):
    def test_finds_manifest_in_project_apm_modules_for_deployed_hook(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            package_root = project_root / "apm_modules" / "lirantal" / "guppi"
            package_root.mkdir(parents=True)
            shutil.copy2(ROOT / "openpeon.json", package_root / "openpeon.json")
            runtime_path = project_root / ".codex" / "hooks" / "guppi" / "guppi_player.py"

            manifest = locate_manifest(
                {"cwd": str(project_root)},
                runtime_path,
                project_root / "global-apm-modules",
            )

            self.assertEqual(manifest.resolve(), (package_root / "openpeon.json").resolve())

    def test_uses_process_working_directory_when_hook_payload_has_no_cwd(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            package_root = project_root / "apm_modules" / "lirantal" / "guppi"
            package_root.mkdir(parents=True)
            shutil.copy2(ROOT / "openpeon.json", package_root / "openpeon.json")
            runtime_path = project_root / ".codex" / "hooks" / "guppi" / "guppi_player.py"
            original_cwd = Path.cwd()
            try:
                os.chdir(project_root)
                manifest = locate_manifest(
                    {}, runtime_path, project_root / "global-apm-modules"
                )
            finally:
                os.chdir(original_cwd)

            self.assertEqual(manifest.resolve(), (package_root / "openpeon.json").resolve())


class PlaybackTests(unittest.TestCase):
    def test_main_plays_stop_event_asynchronously(self):
        calls = []

        result = run_main(
            '{"hook_event_name":"Stop"}',
            {},
            lambda *args, **kwargs: calls.append((args, kwargs)),
        )

        self.assertEqual(result, 0)
        self.assertEqual(calls[0][0][0][0], "afplay")
        self.assertTrue(calls[0][1]["start_new_session"])

    def test_main_ignores_malformed_input(self):
        calls = []

        self.assertEqual(run_main("not json", {}, lambda *args, **kwargs: calls.append(args)), 0)
        self.assertEqual(calls, [])

    def test_main_skips_acknowledgement_until_enabled(self):
        calls = []

        self.assertEqual(
            run_main(
                '{"hook_event_name":"UserPromptSubmit"}',
                {},
                lambda *args, **kwargs: calls.append(args),
            ),
            0,
        )
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
